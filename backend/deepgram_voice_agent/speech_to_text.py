import asyncio
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
import sys
import os

# Add the parent directory to sys.path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DG_API_KEY

load_dotenv()


class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)

transcript_collector = TranscriptCollector()

def get_transcript():
    try:
        # Initialize the Deepgram client with your API key
        deepgram = DeepgramClient(DG_API_KEY)

        # Create a websocket connection
        dg_connection = deepgram.listen.websocket.v("1")

        def on_message(self,result, **kwargs):
            if result.is_final:
                sentence = result.channel.alternatives[0].transcript
                transcript_collector.add_part(sentence)
                print(f"speaker: {transcript_collector.get_full_transcript()}")
                transcript_collector.reset()
            else:
                transcript_collector.add_part(result.channel.alternatives[0].transcript)

        def on_error(self,error, **kwargs):
            print(f"Error: {error}")

        # Attach handlers
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=True
        )

        if dg_connection.start(options) is False:
            print("Failed to connect to Deepgram")
            return


        # Open microphone stream
        microphone = Microphone(dg_connection.send)
        microphone.start()

        input("")

        # Keep script running while mic is active
        microphone.finish()

        microphone.finish()
        dg_connection.finish()

    except Exception as e:
        print(f"Could not open socket: {e}")

if __name__ == "__main__":
    get_transcript()