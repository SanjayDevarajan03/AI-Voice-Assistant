import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import os from "os";

export async function POST(request: NextRequest) {
  try {
    // Process form data and extract the audio file
    const formData = await request.formData();
    const audioFile = formData.get("audio") as File;

    if (!audioFile) {
      return NextResponse.json(
        { error: "No audio file provided" },
        { status: 400 }
      );
    }

    // Create a temporary file to store the audio
    const tempDir = os.tmpdir();
    const tempFilePath = path.join(tempDir, `recording-${Date.now()}.wav`);
    
    // Convert the file to a buffer and write to disk
    const buffer = Buffer.from(await audioFile.arrayBuffer());
    fs.writeFileSync(tempFilePath, buffer);

    // Send to backend processing API
    const formData2 = new FormData();
    formData2.append("audio", new Blob([buffer], { type: "audio/wav" }), "recording.wav");

    // Make request to the backend service
    const backendResponse = await fetch("http://localhost:8000/process-audio", {
      method: "POST",
      body: formData2,
    });

    if (!backendResponse.ok) {
      throw new Error(`Backend error: ${backendResponse.status}`);
    }

    const responseData = await backendResponse.json();

    // Clean up the temporary file
    try {
      fs.unlinkSync(tempFilePath);
    } catch (err) {
      console.error("Error deleting temporary file:", err);
    }

    // Return the response from the backend
    return NextResponse.json({
      response: responseData.text_response,
      audioUrl: responseData.audio_url
    });
  } catch (error) {
    console.error("Error processing audio:", error);
    return NextResponse.json(
      { error: "Failed to process audio" },
      { status: 500 }
    );
  }
} 