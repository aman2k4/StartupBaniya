import os
import srt
from openai_translation import translate_audio
from subtitle_generation import create_subtitles
from video_processing import add_subtitles_to_video
import moviepy.editor as mp

def process_video(input_video_path: str, output_video_path: str, max_words_per_line: int = 4, max_lines: int = 1):
    print(f"Processing video: {input_video_path}")
    
    # Load the video 
    video = mp.VideoFileClip(input_video_path)
    print(f"Video duration: {video.duration} seconds")

    # Get the base filename without extension
    base_filename = os.path.splitext(os.path.basename(input_video_path))[0]

    # Define file paths
    audio_path = f"{base_filename}_audio.mp3"
    translated_text_path = f"{base_filename}_translated.txt"
    srt_path = f"{base_filename}_subtitles.srt"

    # Step 1: Extract audio from video
    if not os.path.exists(audio_path):
        print("Extracting audio...")
        video.audio.write_audiofile(audio_path)
    else:
        print(f"Using existing audio file: {audio_path}")

    # Step 2: Translate audio to English text
    if not os.path.exists(translated_text_path):
        print("Translating audio...")
        translate_audio(audio_path, translated_text_path)
    else:
        print(f"Using existing translated text: {translated_text_path}")

    create_subtitles(translated_text_path, srt_path, max_words_per_line, max_lines, video.duration)

    # Step 4: Add subtitles to video
    print("Adding subtitles to video...")
    add_subtitles_to_video(input_video_path, output_video_path, srt_path)

    print(f"Video processing complete. Output saved as '{output_video_path}'")

# Example usage
if __name__ == "__main__":
    process_video("Day 6.mp4", "Day_6_subtitles.mp4", max_words_per_line=4, max_lines=1)
