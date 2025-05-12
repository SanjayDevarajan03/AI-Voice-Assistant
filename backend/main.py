"""
Main application module for the conversational customer service agent.
This ties together speech-to-text, LLM, and text-to-speech components.
"""
import asyncio
import os
import shutil
import subprocess
import time
import requests
from dotenv import load_dotenv

# Updated imports for LangChain to avoid deprecation warnings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

# Import the correct Deepgram modules
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
)
from deepgram import (
    LiveTranscriptionEvents, 
    LiveOptions,
    Microphone
)

# Load environment variables
load_dotenv()

class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset transcript parts collection."""
        self.transcript_parts = []

    def add_part(self, part):
        """Add a part to the transcript."""
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        """Get the full transcript from all parts."""
        return ' '.join(self.transcript_parts)

class LanguageModelProcessor:
    def __init__(self):
        """
        Initialize the LLM with Groq backend.
        Uses llama3-70b-8192 model for processing chat inputs.
        """
        # Check if API key exists
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not found. Please set it in your .env file.")
            
        # Initialize LLM
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama3-70b-8192", 
            groq_api_key=groq_api_key
        )

        # System prompt for customer service
        self.system_prompt = """  
        You are a helpful and friendly customer service assistant for a cell phone provider.  
        Your goal is to help customers with issues like:
        - Billing questions
        - Troubleshooting their mobile devices
        - Explaining data plans and features
        - Activating or deactivating services
        - Transferring them to appropriate departments for further assistance
        Maintain a polite and professional tone in your responses. Always make the customer feel valued and heard.
        Keep your responses concise as they will be spoken aloud.
        """
        
        # Create the chat history
        self.chat_history = []
        
        # Create the prompt template (avoiding deprecated classes)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{text}")
        ])

    def process(self, text):
        """
        Process user input through the LLM and return the response.
        
        Args:
            text: User input text
            
        Returns:
            LLM response text
        """
        if not text.strip():
            return "I didn't catch that. Could you please repeat?"
            
        # Add user message to chat history
        self.chat_history.append(HumanMessage(content=text))
        
        # Measure response time
        start_time = time.time()
        
        try:
            # Create a runnable chain with the prompt template and LLM
            chain = self.prompt | self.llm
            
            # Process with the chain
            response = chain.invoke({
                "text": text,
                "chat_history": self.chat_history
            })
            
            end_time = time.time()
            
            # Extract the text content from the response
            response_text = response.content
            
            # Add AI response to chat history
            self.chat_history.append(response)
            
            elapsed_time = int((end_time - start_time) * 1000)
            print(f"LLM ({elapsed_time}ms): {response_text}")
            
            return response_text
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "I'm having trouble processing your request right now. Could you try again?"

class TextToSpeech:
    def __init__(self):
        """
        Initialize the Text-to-Speech using Deepgram's API.
        """
        self.dg_api_key = os.getenv("DG_API_KEY")
        if not self.dg_api_key:
            raise ValueError("DG_API_KEY environment variable not found. Please set it in your .env file.")
            
        # Updated to use the current voice model (aura-zeus-en)
        self.model_name = "aura-zeus-en"  # Updated Deepgram TTS voice model
    
    @staticmethod
    def is_installed(lib_name: str) -> bool:
        """Check if a command line utility is installed."""
        lib = shutil.which(lib_name)
        return lib is not None

    def speak(self, text):
        """
        Convert text to speech and play it through the speakers.
        
        Args:
            text: The text to convert to speech
        """
        if not text.strip():
            return
            
        if not self.is_installed("ffplay"):
            print("Warning: ffplay not found. Please install FFmpeg to hear audio output.")
            return
            
        # Prepare API request - Updated URL parameters
        deepgram_url = f"https://api.deepgram.com/v1/speak?model={self.model_name}"
        headers = {
            "Authorization": f"Token {self.dg_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }

        # Start ffplay process for streaming audio
        player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
        try:
            player_process = subprocess.Popen(
                player_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print("Error: Could not start ffplay. Make sure FFmpeg is installed correctly.")
            return

        # Timing metrics
        start_time = time.time()
        first_byte_time = None

        try:
            # Stream audio data to ffplay
            with requests.post(deepgram_url, stream=True, headers=headers, json=payload) as r:
                if r.status_code != 200:
                    print(f"TTS API error: {r.status_code} - {r.text}")
                    player_process.terminate()
                    return
                
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        if first_byte_time is None:
                            first_byte_time = time.time()
                            ttfb = int((first_byte_time - start_time)*1000)
                            print(f"TTS Time to First Byte (TTFB): {ttfb}ms\n")
                        player_process.stdin.write(chunk)
                        player_process.stdin.flush()

            # Clean up
            if player_process.stdin:
                player_process.stdin.close()
            player_process.wait()
            
        except requests.exceptions.RequestException as e:
            print(f"Error with TTS request: {e}")
            if player_process.stdin:
                player_process.stdin.close()
            player_process.terminate()

class SpeechRecognizer:
    def __init__(self):
        """
        Initialize the Speech-to-Text component with Deepgram.
        """
        self.api_key = os.getenv("DG_API_KEY")
        if not self.api_key:
            raise ValueError("DG_API_KEY environment variable not found. Please set it in your .env file.")
            
        self.transcript_collector = TranscriptCollector()
        
    async def listen_for_speech(self, callback):
        transcription_complete = asyncio.get_event_loop().create_future()

        try:
            config = DeepgramClientOptions(options={"keepalive": "true"})
            deepgram = DeepgramClient(self.api_key, config)
            dg_connection = deepgram.listen.websocket.v("1")
            print("Listening...")

            async def on_message(self, result, **kwargs):
                if not hasattr(result, 'channel') or not hasattr(result.channel, 'alternatives') or len(result.channel.alternatives) == 0:
                    return

                sentence = result.channel.alternatives[0].transcript

                if not result.speech_final:
                    self.transcript_collector.add_part(sentence)
                else:
                    self.transcript_collector.add_part(sentence)
                    full_sentence = self.transcript_collector.get_full_transcript()

                    if full_sentence.strip():
                        print(f"Human: {full_sentence}")
                        callback(full_sentence)
                        self.transcript_collector.reset()
                        if not transcription_complete.done():
                            transcription_complete.set_result(True)

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                endpointing=300,
                smart_format=True,
            )

            await dg_connection.start(options)

            microphone = Microphone(dg_connection.send)
            microphone.start()

            transcription_complete.set() 
            await transcription_complete.wait()

            microphone.finish()
            await dg_connection.finish()

        except Exception as e:
            print(f"Error in speech recognition: {e}")
            if not transcription_complete.done():
                transcription_complete.set_result(True)

class ConversationManager:
    def __init__(self):
        """Initialize the conversation manager with all components."""
        self.llm = LanguageModelProcessor()
        self.tts = TextToSpeech()
        self.speech_recognizer = SpeechRecognizer()
        self.transcription_response = ""
        self.is_running = True

    def handle_full_sentence(self, full_sentence):
        """Handle a complete transcribed sentence."""
        self.transcription_response = full_sentence

    async def main(self):
        """Main conversation loop."""
        # Welcome message
        welcome_message = "Hello! I'm your cell phone provider's virtual assistant. How can I help you today?"
        print(f"Assistant: {welcome_message}")
        self.tts.speak(welcome_message)
        
        # Main conversation loop
        while self.is_running:
            try:
                # Reset the transcription response
                self.transcription_response = ""
                
                # Listen for speech
                await self.speech_recognizer.listen_for_speech(self.handle_full_sentence)
                
                # Check for exit commands
                if self.transcription_response.lower() in ["goodbye", "exit", "quit", "bye"]:
                    farewell = "Thank you for contacting customer service. Have a great day!"
                    print(f"Assistant: {farewell}")
                    self.tts.speak(farewell)
                    self.is_running = False
                    break
                
                # Process the transcription through the LLM
                if self.transcription_response:
                    llm_response = self.llm.process(self.transcription_response)
                    
                    # Speak the response
                    self.tts.speak(llm_response)
                
            except KeyboardInterrupt:
                print("\nStopping the conversation...")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error in conversation loop: {e}")
                # Continue the loop to keep the conversation going despite errors


if __name__ == "__main__":
    
    try:
        # Start the conversation manager
        manager = ConversationManager()
        asyncio.run(manager.main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")