import httpx
import json
import speech_recognition as sr
import tempfile
import os
from pydub import AudioSegment
from elevenlabs import generate, clone, set_api_key, Voice, VoiceSettings
from openai import OpenAI
from app.config import OPENROUTER_API_KEY, ELEVENLABS_API_KEY, OPENAI_API_KEY

# Initialize services
if ELEVENLABS_API_KEY:
    set_api_key(ELEVENLABS_API_KEY)

class SpeechToTextService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Convert audio to text using OpenAI Whisper"""
        try:
            if self.openai_client:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text.strip()
            else:
                # Fallback to Google Speech Recognition
                with sr.AudioFile(audio_file_path) as source:
                    audio_data = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio_data)
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

class SpeechAnalysisService:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "mistralai/mistral-7b-instruct"
    
    async def analyze_speech(self, text: str) -> dict:
        """Analyze speech and generate alternatives"""
        prompt = f"""
        Analyze this speech and provide a JSON response:

        Speech: "{text}"

        Return JSON in this exact format:
        {{
            "category": "The main category (politics, economics, climate, etc.)",
            "demographics": ["3 different demographic perspectives"],
            "alternateSpeeches": [
                {{
                    "demographic": "First demographic",
                    "speech": "Rewritten speech for this demographic in 2-3 sentences"
                }},
                {{
                    "demographic": "Second demographic", 
                    "speech": "Rewritten speech for this demographic in 2-3 sentences"
                }},
                {{
                    "demographic": "Third demographic",
                    "speech": "Rewritten speech for this demographic in 2-3 sentences"
                }}
            ]
        }}

        Only return the JSON, no other text.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except:
                # Fallback response
                return {
                    "category": "General",
                    "demographics": ["Progressive", "Conservative", "Moderate"],
                    "alternateSpeeches": [
                        {
                            "demographic": "Progressive",
                            "speech": "We need bold action and systemic change to address this issue effectively."
                        },
                        {
                            "demographic": "Conservative", 
                            "speech": "We should preserve our values while making careful, measured improvements."
                        },
                        {
                            "demographic": "Moderate",
                            "speech": "A balanced approach considering all perspectives will yield the best results."
                        }
                    ]
                }

class VoiceService:
    def __init__(self):
        self.user_voice_id = None
    
    async def clone_voice(self, audio_file_path: str) -> str:
        """Clone user's voice"""
        try:
            voice = clone(
                name="User Voice",
                description="User's cloned voice",
                files=[audio_file_path]
            )
            self.user_voice_id = voice.voice_id
            return voice.voice_id
        except Exception as e:
            print(f"Voice cloning error: {e}")
            return None
    
    async def generate_speech(self, text: str, use_user_voice: bool = False) -> bytes:
        """Generate speech audio"""
        try:
            if use_user_voice and self.user_voice_id:
                voice_id = self.user_voice_id
            else:
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice
            
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.75,
                        similarity_boost=0.75
                    )
                )
            )
            return audio
        except Exception as e:
            print(f"Speech generation error: {e}")
            return None

# Initialize services
speech_to_text = SpeechToTextService()
speech_analysis = SpeechAnalysisService()
voice_service = VoiceService()