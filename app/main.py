from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import tempfile
import os
import io
from app.services import speech_analysis, voice_service

app = FastAPI(title="ClarityAI MVP Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ClarityAI MVP Backend"}

@app.post("/analyze")
async def analyze_speech(request_data: dict):
    """Analyze speech and generate alternatives"""
    try:
        text = request_data.get("text", "")
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        print(f"Analyzing text: {text[:100]}...")
        analysis = await speech_analysis.analyze_speech(text)
        print(f"Analysis completed: {analysis}")
        return analysis
    
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clone-voice")
async def clone_voice(audio_file: UploadFile = File(...)):
    """Clone user's voice"""
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Clone voice
        voice_id = await voice_service.clone_voice(tmp_file_path)
        
        # Cleanup
        os.unlink(tmp_file_path)
        
        if not voice_id:
            raise HTTPException(status_code=400, detail="Could not clone voice")
        
        return {"voice_id": voice_id, "message": "Voice cloned successfully"}
    
    except Exception as e:
        print(f"Voice cloning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio")
async def generate_audio(text: str, use_user_voice: bool = False):
    """Generate speech audio"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        print(f"Generating audio for: {text[:50]}...")
        audio_data = await voice_service.generate_speech(text, use_user_voice)
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Could not generate audio")
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    
    except Exception as e:
        print(f"Audio generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)