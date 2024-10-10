import srt
import datetime
from typing import List

def split_text_into_subtitles(max_words_per_line: int, max_lines: int) -> List[str]:
    with open("translated_audio.txt", "r") as file:
        text = file.read()

    words = text.split()
    subtitles = []
    current_subtitle = []
    current_line = []

    for word in words:
        if len(current_line) >= max_words_per_line:
            current_subtitle.append(' '.join(current_line))
            current_line = []
        
        current_line.append(word)
        
        if len(current_subtitle) >= max_lines:
            subtitles.append('\n'.join(current_subtitle))
            current_subtitle = []

    # Add any remaining lines to the current subtitle
    if current_line:
        current_subtitle.append(' '.join(current_line))
    
    # Add any remaining subtitle to the list
    if current_subtitle:
        subtitles.append('\n'.join(current_subtitle))

    # save the subtitle parts in a txt file 
    with open("subtitle_parts.txt", "w") as file:
        file.write(str(subtitles))

    return subtitles

def create_subtitles(max_words_per_line: int, max_lines: int, video_duration: float) -> List[srt.Subtitle]:
    # First, split the text into subtitle parts
    subtitle_parts = split_text_into_subtitles(max_words_per_line, max_lines)
    
    subtitles = []
    time_per_subtitle = video_duration / len(subtitle_parts)
    
    for i, part in enumerate(subtitle_parts):
        start = datetime.timedelta(seconds=i * time_per_subtitle)
        end = datetime.timedelta(seconds=(i + 1) * time_per_subtitle)
        subtitles.append(srt.Subtitle(index=i+1, start=start, end=end, content=part))
    
    # save it in a srt file 
    with open("subtitles.srt", "w") as file:
        file.write(srt.compose(subtitles))
    
    return subtitles