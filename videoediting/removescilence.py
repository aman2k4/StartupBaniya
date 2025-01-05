from moviepy.editor import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment, silence
import os
import json

def remove_silent_parts(input_video, output_video, config_file='silence_config.json'):
    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    silence_thresh = config.get('silence_thresh', -40)
    min_silence_len = config.get('min_silence_len', 500)
    
    # Load the video file
    video = VideoFileClip(input_video)
    
    # Extract audio
    audio = video.audio
    audio_file = "temp_audio.wav"
    audio.write_audiofile(audio_file)
    
    # Use pydub to detect silence in the audio
    sound = AudioSegment.from_wav(audio_file)
    non_silent_ranges = silence.detect_nonsilent(sound, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    
    # Convert pydub time format (ms) to seconds and create clips without silent parts
    video_clips = [video.subclip(start / 1000, end / 1000) for start, end in non_silent_ranges]
    
    # Concatenate all non-silent clips
    final_video = concatenate_videoclips(video_clips)
    
    # Save the result with audio
    final_video.write_videofile(output_video, audio_codec='aac')
    
    # Clean up temporary files
    os.remove(audio_file)
    video.close()
    final_video.close()

# Example usage
input_video = "C1285.MP4"
output_video = "output_without_silence.mp4"
remove_silent_parts(input_video, output_video)
