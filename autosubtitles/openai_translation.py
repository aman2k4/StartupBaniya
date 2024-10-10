from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def translate_audio(file_path: str, translation_file: str) -> str:
    print("Translating audio to English...")
    with open(file_path, 'rb') as audio_file:
        translation = client.audio.translations.create(
            model="whisper-1", 
            file=audio_file
        )
    print("Audio translated.")
    # save it in a txt file 
    with open(translation_file, "w") as file:
        file.write(translation.text)
    return translation.text