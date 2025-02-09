#!/usr/bin/env python3
"""
Real-time French-to-English translation using Moshi MLX inference.

This script captures microphone audio in real time, performs inference using
the Moshi/Mimi model pipeline, prints the translated text, and plays back the
synthesized audio. It reuses the inference logic from run_inference.py.
"""

import argparse
import json
import numpy as np
import time
import sounddevice as sd

from huggingface_hub import hf_hub_download
import mlx.core as mx
import mlx.nn as nn
import rustymimi
import sentencepiece
# We do not need sphn since we are not decoding a file
from moshi_mlx.client_utils import make_log
from moshi_mlx import models, utils


def log(level: str, msg: str):
    print(make_log(level, msg))


def hf_get(filename: str) -> str:
    if filename.startswith("hf://"):
        parts = filename[5:].split("/")
        repo_name = parts[0] + "/" + parts[1]
        filename = "/".join(parts[2:])
        log("info", f"retrieving {filename} from hf repo {repo_name}")
        return hf_hub_download(repo_name, filename)
    else:
        return filename


def main():
    parser = argparse.ArgumentParser(
        description="Real-time French-to-English translation using microphone input"
    )
    parser.add_argument("--tokenizer", type=str, help="Path to the text tokenizer file")
    parser.add_argument("--moshi-weights", type=str, help="Path to a local checkpoint file for Moshi.")
    parser.add_argument("--mimi-weights", type=str, help="Path to a local checkpoint file for Mimi.")
    parser.add_argument("--hf-repo", type=str, default="kyutai/hibiki-1b-mlx-bf16", help="HuggingFace repo name")
    parser.add_argument("--lm-config", type=str, help="The LM config as a json file.")
    parser.add_argument("--cfg-coef", type=float, default=1.0, help="CFG coefficient")
    parser.add_argument("--device", type=str, default=None, help="Audio device for playback (optional)")
    parser.add_argument("--input-device", type=str, default=None, help="Audio input device (microphone)")
    args = parser.parse_args()

    # Set audio processing parameters
    sample_rate = 24000  # in Hz
    block_size = 1920    # number of samples per inference step (≈80ms)

    mx.random.seed(299792458)

    # Load LM config
    lm_config = args.lm_config
    if lm_config is None:
        # Download config.json from the HuggingFace repo
        lm_config = hf_hub_download(args.hf_repo, "config.json")
    log("info", f"loading config from {args.lm_config}")
    with open(hf_get(lm_config), "r") as fobj:
        lm_config_dict = json.load(fobj)
    print(lm_config_dict)

    # Get weight files
    mimi_weights = args.mimi_weights
    if mimi_weights is None:
        mimi_weights = hf_hub_download(args.hf_repo, lm_config_dict["mimi_name"])
    mimi_weights = hf_get(mimi_weights)

    moshi_weights = args.moshi_weights
    if moshi_weights is None:
        moshi_weights = hf_hub_download(args.hf_repo, lm_config_dict["moshi_name"])
    moshi_weights = hf_get(moshi_weights)

    tokenizer = args.tokenizer
    if tokenizer is None:
        tokenizer = hf_hub_download(args.hf_repo, lm_config_dict["tokenizer_name"])
    tokenizer = hf_get(tokenizer)

    # Load model configuration and create the model
    lm_config = models.LmConfig.from_config_dict(lm_config_dict)
    model = models.Lm(lm_config)
    model.set_dtype(mx.bfloat16)
    if moshi_weights.endswith(".q4.safetensors"):
        nn.quantize(model, bits=4, group_size=32)
    elif moshi_weights.endswith(".q8.safetensors"):
        nn.quantize(model, bits=8, group_size=64)

    log("info", f"loading model weights from {moshi_weights}")
    model.load_weights(moshi_weights, strict=True)

    log("info", f"loading the text tokenizer from {tokenizer}")
    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)

    log("info", f"loading the audio tokenizer from {mimi_weights}")
    generated_codebooks = lm_config.generated_codebooks
    audio_tokenizer = rustymimi.Tokenizer(mimi_weights, num_codebooks=generated_codebooks)

    if model.condition_provider is not None:
        ct = model.condition_provider.condition_tensor("description", "very_good")
    else:
        ct = None

    log("info", "warming up the model")
    model.warmup(ct)
    log("info", "done warming up the model")

    # Create the generator for text and audio tokens.
    # Set max_steps high enough for continuous streaming.
    gen = models.LmGen(
        model=model,
        max_steps=100000,
        text_sampler=utils.Sampler(top_k=25),
        audio_sampler=utils.Sampler(top_k=250),
        cfg_coef=args.cfg_coef,
        check=False,
    )

    # --- Callback Function ---
    def audio_callback(indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)
        # indata shape: (frames, num_channels)  <--  (block_size, 1) in our case

        # VU Meter (Feedback)
        volume_norm = np.linalg.norm(indata) * 10
        print("|" + "*" * int(volume_norm) + "-" * (10 - int(volume_norm)) + "|")

        # Prepare the audio block (reshape as needed)
        # The audio block shape is (block_size, 1). Transpose to (1, block_size)
        pcm_data = indata.T

        # The encoder expects an input shape of (batch, channel, samples)
        encoded = audio_tokenizer.encode_step(pcm_data[None, 0:1])
        encoded = mx.array(encoded).transpose(0, 2, 1)[:, :, :generated_codebooks]

        # Generate the next text token using the model
        text_token = gen.step(encoded[0], ct)
        text_token = text_token[0].item()

        # Print the translated text if it is meaningful
        if text_token not in (0, 3):
            text_piece = text_tokenizer.id_to_piece(text_token)
            text_piece = text_piece.replace(" ", " ")
            print(text_piece, end="", flush=True)

        # Get the audio tokens produced in this step and decode them
        audio_tokens = gen.last_audio_tokens()
        if audio_tokens is not None:
            audio_tokens = np.array(audio_tokens[:, :, None]).astype(np.uint32)
            out_pcm = audio_tokenizer.decode_step(audio_tokens)
            # out_pcm is expected to be of shape (channels, samples)
            # Transpose to (samples, channels) for sd.play()
            out_pcm = out_pcm.T
            if out_pcm.shape[1] == 1:  # Check for mono output
                out_pcm = out_pcm[:, 0]  # Squeeze to one dimension
            if args.device:
                sd.play(out_pcm, samplerate=sample_rate, device=args.device)
            else:
                sd.play(out_pcm, samplerate=sample_rate)
            sd.wait()  # Wait until playback is finished


    # --- Start the Stream ---
    log("info", "starting real-time inference. Press Ctrl+C to stop.")
    try:
        with sd.InputStream(
            device=args.input_device,
            samplerate=sample_rate,
            blocksize=block_size,
            channels=1,
            dtype='float32',
            callback=audio_callback
        ):
            while True: # Keep the main thread alive
                time.sleep(0.1) #  Avoid busy-waiting

    except KeyboardInterrupt:
        log("info", "Real-time inference stopped by user.")
    except Exception as e:
        log("error", str(e))


if __name__ == "__main__":
    main()
