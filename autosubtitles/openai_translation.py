from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def translate_audio(file_path: str, translation_file: str) -> str:
    print(f"Translating audio to English: {file_path}")
    with open(file_path, 'rb') as audio_file:
        translation = client.audio.translations.create(
            model="whisper-1", 
            file=audio_file
        )
    print(f"Audio translated. Saving to: {translation_file}")
    # save it in a txt file 
    with open(translation_file, "w") as file:
        file.write(translation.text)
    return translation.text
