import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Voice Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys
DG_API_KEY = os.getenv("DG_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DG_API_KEY or not GROQ_API_KEY:
    raise ValueError("Please set the DG_API_KEY and GROQ_API_KEY environment variables.")

# Initialize clients
deepgram = DeepgramClient(DG_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Create static folder for audio responses
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# System prompt for customer service
system_prompt = """
You are a helpful and friendly customer service assistant for a cell phone provider. Your goal is to help customers with issues like:
- Billing questions
- Troubleshooting their mobile devices
- Explaining data plans and features
- Activating or deactivating services
- Transferring them to appropriate departments for further assistance.

Maintain a polite and professional tone in your responses. Always make the customer feel valued and heard.
Be concise but thorough in your response.
"""

# Deepgram options
text_options = PrerecordedOptions(
    model="nova-2",
    language="en",
    smart_format=True,
)

speak_options = SpeakOptions(
    model="aura-asteria-en",
    encoding="linear16",
    container="wav"
)

class TranscriptionResponse(BaseModel):
    text: str

async def transcribe_audio(audio_file_path):
    """Transcribe audio using Deepgram"""
    with open(audio_file_path, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = deepgram.listen.rest.v("1").transcribe_file(source, text_options)
        transcript = json.loads(response.to_json())
        
        if "results" in transcript and "channels" in transcript["results"]:
            transcription = transcript["results"]["channels"][0]["alternatives"][0]["transcript"]
            return transcription
        else:
            return ""

async def get_ai_response(transcript):
    """Get response from Groq LLM"""
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ],
        model="deepseek-r1-distill-llama-70b",
        temperature=0.7
    )
    return response.choices[0].message.content

async def text_to_speech(text):
    """Convert text to speech using Deepgram"""
    text_payload = {"text": text}
    filename = f"static/audio/response-{uuid.uuid4()}.wav"
    response = deepgram.speak.rest.v("1").save(filename, text_payload, speak_options)
    return filename

@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    """Process audio, transcribe, get AI response, and convert to speech"""
    try:
        # Save uploaded audio to temp file
        audio_file_path = f"temp-audio-{uuid.uuid4()}.wav"
        with open(audio_file_path, "wb") as buffer:
            buffer.write(await audio.read())
        
        # Transcribe audio
        transcript = await transcribe_audio(audio_file_path)
        if not transcript:
            raise HTTPException(status_code=400, detail="Failed to transcribe audio")
        
        # Get AI response
        text_response = await get_ai_response(transcript)
        
        # Convert to speech
        audio_file = await text_to_speech(text_response)
        
        # Clean up temp file
        os.remove(audio_file_path)
        
        # Return response
        return JSONResponse({
            "transcript": transcript,
            "text_response": text_response,
            "audio_url": f"/{audio_file}"
        })
    
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
