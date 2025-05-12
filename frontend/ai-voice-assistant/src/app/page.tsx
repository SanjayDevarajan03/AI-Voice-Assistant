"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [response, setResponse] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setAudioBlob(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error starting recording:", err);
      setError("Microphone access denied. Please allow microphone access.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleSubmit = async () => {
    if (!audioBlob) return;

    try {
      setIsLoading(true);
      setError(null);
      
      // Create form data to send
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.wav");

      // Send to backend API
      const response = await fetch("/api/process-voice", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setResponse(data.response);
      
      // Play audio response if available
      if (data.audioUrl) {
        const audio = new Audio(data.audioUrl);
        audio.play();
      }
    } catch (err) {
      console.error("Error submitting audio:", err);
      setError("Failed to process your request. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex flex-col items-center p-6">
      <header className="w-full max-w-4xl mb-12 pt-8">
        <h1 className="text-3xl font-bold text-center text-blue-600 dark:text-blue-400">
          AI Customer Service Assistant
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-300 mt-2">
          Ask about your phone bill, data plan, or any other account issues
        </p>
      </header>

      <main className="flex-1 w-full max-w-4xl flex flex-col items-center">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full p-6 mb-8">
          <div className="flex flex-col items-center justify-center space-y-6">
            <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-blue-500'}`}>
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className="w-full h-full rounded-full flex items-center justify-center text-white focus:outline-none"
              >
                {isRecording ? (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 7.5A2.25 2.25 0 0 1 7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9Z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="text-gray-600 dark:text-gray-300">
              {isRecording ? "Recording... Click to stop" : "Tap microphone to speak"}
            </p>

            {audioBlob && !isRecording && (
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
              >
                {isLoading ? "Processing..." : "Submit Recording"}
              </button>
            )}

            {error && (
              <div className="text-red-500 text-center p-2 bg-red-50 dark:bg-red-900/20 rounded-lg w-full">
                {error}
              </div>
            )}
          </div>
        </div>

        {response && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg w-full p-6 mb-8">
            <h2 className="text-lg font-medium mb-4 text-gray-800 dark:text-gray-200">Response:</h2>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{response}</p>
          </div>
        )}

        <div className="bg-blue-50 dark:bg-gray-700/50 rounded-2xl p-6 w-full">
          <h2 className="text-lg font-medium mb-4 text-gray-800 dark:text-gray-200">Example Questions:</h2>
          <ul className="space-y-2 text-gray-700 dark:text-gray-300">
            <li>"Why is my bill higher this month?"</li>
            <li>"Can you explain my data usage?"</li>
            <li>"How do I upgrade my plan?"</li>
            <li>"When will my payment be processed?"</li>
            <li>"I need help troubleshooting my device."</li>
          </ul>
        </div>
      </main>

      <footer className="w-full max-w-4xl mt-12 pt-6 border-t border-gray-200 dark:border-gray-700">
        <p className="text-center text-gray-500 dark:text-gray-400 text-sm">
          © 2024 AI Voice Assistant. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
