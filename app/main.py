from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services import speech_analysis

app = FastAPI(title="ClarityAI Text Analysis Backend")

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
    return {"message": "ClarityAI Text Analysis Backend"}

@app.post("/analyze")
async def analyze_speech(request_data: dict):
    """Analyze speech and generate alternatives"""
    try:
        text = request_data.get("text", "")
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        print(f"Analyzing text: {text[:100]}...")
        analysis = await speech_analysis.analyze_speech(text)
        print(f"Analysis completed successfully")
        return analysis
    
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)