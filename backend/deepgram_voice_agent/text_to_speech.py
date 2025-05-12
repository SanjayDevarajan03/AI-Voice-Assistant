import os
import requests
from dotenv import load_dotenv
import subprocess
import shutil
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DG_API_KEY

# Loading the environment variables
load_dotenv()

if not DG_API_KEY:
    raise ValueError("DG_API_KEY environment variable is not set")

def is_installed(lib_name: str) -> bool:
    lib = shutil.which(lib_name)
    return lib is not None

def save_and_play_audio(text):
    """Send a TTS request to Deepgram, save the response, and play it with ffplay."""
    DEEPGRAM_URL = "https://api.deepgram.com/v1/speak"
    
    headers = {
        "Authorization": f"Token {DG_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using the simplest possible payload
    payload = {
        "text": text
    }

    if not is_installed("ffplay"):
        raise ValueError("ffplay not found. Ensure FFmpeg is installed and ffplay is in your PATH.")

    # File to save audio for debugging
    output_file = "output.wav"
    
    print(f"Sending request to {DEEPGRAM_URL} with text: '{text}'")
    
    try:
        # Send POST request to Deepgram
        response = requests.post(DEEPGRAM_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Deepgram API error: {response.status_code} - {response.text}")
            return False
        
        # Save the audio response to a file
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"Audio saved to {output_file}")
        
        # Play the audio file
        print("Playing audio...")
        subprocess.run(["ffplay", "-autoexit", "-nodisp", output_file])
        
        return True
    
    except Exception as e:
        print(f"Error during TTS request: {e}")
        return False

# Example usage
if __name__ == "__main__":
    text = "Hello, this is a test of Deepgram text-to-speech."
    success = save_and_play_audio(text)

