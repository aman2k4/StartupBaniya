from openai import OpenAI
import moviepy.editor as mp
import srt
import datetime
from typing import List
import math
import os
from dotenv import load_dotenv
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def translate_audio(file_path: str) -> str:
    print("Translating audio to English...")
    with open(file_path, 'rb') as audio_file:
        translation = client.audio.translations.create(
            model="whisper-1", 
            file=audio_file
        )
    print("Audio translated.")
    return translation.text

def split_text_into_subtitles(text: str, max_words: int) -> List[str]:
    words = text.split()
    subtitles = []
    for i in range(0, len(words), max_words):
        line = ' '.join(words[i:i+max_words])
        if len(subtitles) > 0 and len(subtitles[-1].split('\n')) < 2:
            # If the previous subtitle has only one line, try to add this line to it
            combined = subtitles[-1] + '\n' + line
            if len(combined.split()) <= max_words * 2:
                subtitles[-1] = combined
                continue
        subtitles.append(line)
    return subtitles

def create_subtitles(subtitle_parts: List[str], video_duration: float) -> List[srt.Subtitle]:
    subtitles = []
    time_per_subtitle = video_duration / len(subtitle_parts)
    
    for i, part in enumerate(subtitle_parts):
        start = datetime.timedelta(seconds=i * time_per_subtitle)
        end = datetime.timedelta(seconds=(i + 1) * time_per_subtitle)
        subtitles.append(srt.Subtitle(index=i, start=start, end=end, content=part))
    
    return subtitles

def create_subtitle_clip(txt, video_width, video_height):
    fontsize = 60
    font = 'Arial-Bold'
    
    # Calculate the maximum width for the subtitle box (80% of video width)
    max_box_width = int(video_width * 0.8)
    
    # Create text clip
    txt_clip = mp.TextClip(txt, fontsize=fontsize, font=font, color='white', stroke_color='black', 
                           stroke_width=3, method='caption', align='center', size=(max_box_width, None))
    
    # Create background clip
    txt_width, txt_height = txt_clip.size
    background_width = max_box_width  # Set to 80% of video width
    background_height = txt_height + 20  # Add padding
    
    # Create a rounded rectangle background using PIL
    background = Image.new('RGBA', (background_width, background_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(background)
    draw.rounded_rectangle([(0, 0), (background_width, background_height)], radius=15, fill=(128, 128, 128, 200))
    
    # Convert PIL Image to numpy array
    background_array = np.array(background)
    
    # Create MoviePy clip from the numpy array
    background_clip = mp.ImageClip(background_array).set_duration(txt_clip.duration)

    # Composite text over background
    composite = mp.CompositeVideoClip([background_clip, txt_clip.set_position('center')])
    
    # Set position to center of video
    composite = composite.set_position(('center', 'center'))
    
    return composite

def add_subtitles_to_video(input_video_path: str, output_video_path: str, max_words_per_subtitle: int = 7):
    print(f"Processing video: {input_video_path}")
    # Load the video
    video = mp.VideoFileClip(input_video_path)
    print(f"Video duration: {video.duration} seconds")

    srt_path = "subtitles.srt"

    if not os.path.exists(srt_path):
        print("Generating new subtitles...")
        # Extract audio from video
        audio_path = "temp_audio.mp3"
        video.audio.write_audiofile(audio_path)

        # Translate audio to English text
        translated_text = translate_audio(audio_path)
        print(f"Translated text (first 100 chars): {translated_text[:100]}...")

        # Split translated text into subtitles
        subtitle_parts = split_text_into_subtitles(translated_text, max_words_per_subtitle)
        print(f"Number of subtitle parts: {len(subtitle_parts)}")

        # Create subtitle objects
        subtitles = create_subtitles(subtitle_parts, video.duration)

        # Generate SRT file
        with open(srt_path, "w") as srt_file:
            srt_file.write(srt.compose(subtitles))

        # Clean up temporary audio file
        os.remove(audio_path)
    else:
        print(f"Using existing {srt_path} file.")

    # Print contents of SRT file
    with open(srt_path, "r") as srt_file:
        srt_content = srt_file.read()
        print(f"SRT file contents (first 500 chars):\n{srt_content[:500]}...")

    # Create a SubtitlesClip with adjusted style
    generator = lambda txt: create_subtitle_clip(txt, video.w, video.h)
    subtitles_clip = SubtitlesClip(srt_path, generator)
    print(f"Subtitles clip duration: {subtitles_clip.duration} seconds")

    # Overlay subtitles on the video
    final_video = CompositeVideoClip([video, subtitles_clip.set_position(('center', 'center'))])
    print(f"Final video duration: {final_video.duration} seconds")

    # Write the final video
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    # Clean up temporary files
    # os.remove(audio_path)
    # os.remove(srt_path)

    print(f"Video processing complete. Output saved as '{output_video_path}'")

# Example usage
add_subtitles_to_video("1003.mp4", "output_with_subtitles.mp4", max_words_per_subtitle=7)