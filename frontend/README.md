# AI Voice Assistant

A web application that allows users to speak with an AI customer service assistant that can answer questions about their phone account, billing, data plans, and more.

## Features

- Voice recording directly in the browser
- Speech-to-text transcription using Deepgram
- AI responses using Groq's large language models
- Text-to-speech for AI responses

## Prerequisites

- Node.js 18+ for the frontend
- Python 3.8+ for the backend
- Deepgram API key (https://deepgram.com)
- Groq API key (https://groq.com)

## Setup

### Environment Variables

1. Create a `.env` file in the root directory
2. Add your API keys:
   ```
   DG_API_KEY=your_deepgram_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

### Backend Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```
   python app.py
   ```
   The backend will run on http://localhost:8000

### Frontend Setup

1. Navigate to the ai-voice-assistant directory:
   ```
   cd ai-voice-assistant
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```
   The frontend will run on http://localhost:3000

## Usage

1. Open the web application in your browser
2. Click the microphone button to start recording
3. Speak your question or issue related to your phone service
4. Click the microphone button again to stop recording
5. Click "Submit Recording" to send the audio for processing
6. The AI will respond with both text and voice

## API Endpoints

- `POST /process-audio`: Accepts an audio file, transcribes it, generates an AI response, and converts the response to speech

## Technologies Used

- Frontend: Next.js, React, TailwindCSS
- Backend: FastAPI, Deepgram SDK, Groq API
- Voice Processing: Deepgram Nova-2 for transcription, Groq for AI, Deepgram Aura for speech synthesis 