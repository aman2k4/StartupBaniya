import srt
import datetime
import json
from typing import List
from openai import OpenAI
from pydantic import BaseModel, Field

class ProcessedText(BaseModel):
    sentences: List[str] = Field(..., description="An array of corrected and split sentences from the input text")

def process_text_with_llm(text: str) -> List[str]:
    client = OpenAI()
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",  # Update this to the latest available model
        messages=[
            {
                "role": "system",
                "content": "You are an expert in creating subtitles for videos in a mix of Hindi and English. Your task is to correct the grammar and improve the tonality of the provided text, splitting it into clear and concise sentences. Each sentence should be easy to read, grammatically correct, and maintain the original meaning and tone of the video. Avoid using full stops at the end of sentences."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.0,
        response_format=ProcessedText,
    )

    processed_text = completion.choices[0].message.parsed
    return processed_text.sentences

def create_subtitles(translated_text_path: str, srt_path: str, max_words_per_line: int, max_lines: int, video_duration: float) -> List[srt.Subtitle]:
    # Read the translated text
    with open(translated_text_path, "r") as file:
        text = file.read()
    
    # Process the text with LLM
    processed_sentences = process_text_with_llm(text)
    
    # Save processed sentences to a file
    processed_sentences_path = srt_path.replace('.srt', '_processed.json')
    with open(processed_sentences_path, "w") as file:
        json.dump({"sentences": processed_sentences}, file, indent=2)
    
    # Create subtitle parts from processed sentences
    subtitle_parts = []
    current_part = []
    current_line_count = 0
    
    for sentence in processed_sentences:
        words = sentence.split()
        current_line = []
        
        for word in words:
            if len(current_line) >= max_words_per_line:
                current_part.append(' '.join(current_line))
                current_line = []
                current_line_count += 1
            
            current_line.append(word)
            
            if current_line_count >= max_lines:
                subtitle_parts.append('\n'.join(current_part))
                current_part = []
                current_line_count = 0
        
        if current_line:
            current_part.append(' '.join(current_line))
            current_line_count += 1
    
    if current_part:
        subtitle_parts.append('\n'.join(current_part))
    
    # Create SRT subtitles
    subtitles = []
    time_per_subtitle = video_duration / len(subtitle_parts)
    
    for i, part in enumerate(subtitle_parts):
        start = datetime.timedelta(seconds=i * time_per_subtitle)
        end = datetime.timedelta(seconds=(i + 1) * time_per_subtitle)
        subtitles.append(srt.Subtitle(index=i+1, start=start, end=end, content=part))
    
    # Save subtitles to SRT file
    with open(srt_path, "w") as file:
        file.write(srt.compose(subtitles))
    
    return subtitles

# Remove or comment out the split_text_into_subtitles function as it's no longer needed
