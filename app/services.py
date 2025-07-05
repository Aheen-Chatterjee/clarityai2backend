import httpx
import json
import tempfile
import os
import requests
from elevenlabs import generate, clone, set_api_key, Voice, VoiceSettings
from app.config import OPENROUTER_API_KEY, ELEVENLABS_API_KEY

print(f"OpenRouter API Key configured: {bool(OPENROUTER_API_KEY)}")
print(f"ElevenLabs API Key configured: {bool(ELEVENLABS_API_KEY)}")

# Initialize services
if ELEVENLABS_API_KEY:
    set_api_key(ELEVENLABS_API_KEY)

class SpeechToTextService:
    def __init__(self):
        pass
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Simple placeholder - actual transcription will be done in frontend"""
        try:
            # For now, return a message indicating frontend should handle this
            return "Speech transcription will be handled by the browser"
        except Exception as e:
            print(f"Transcription error: {e}")
            return "Transcription failed"

class SpeechAnalysisService:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "mistralai/mistral-7b-instruct"
    
    async def analyze_speech(self, text: str) -> dict:
        """Analyze speech and generate alternatives"""
        
        if not self.api_key:
            print("ERROR: No OpenRouter API key configured!")
            return self._fallback_response()
        
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
                    "speech": "Rewritten speech for this demographic, considering what they care about. Match length of original speech."
                }},
                {{
                    "demographic": "Second demographic", 
                    "speech": "Rewritten speech for this demographic, considering what they care about. Match length of original speech."
                }},
                {{
                    "demographic": "Third demographic",
                    "speech": "Rewritten speech for this demographic, considering what they care about. Match length of original speech."
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

        try:
            print(f"Making request to OpenRouter...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                print(f"OpenRouter response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"OpenRouter error: {response.text}")
                    return self._fallback_response()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    parsed_result = json.loads(content)
                    print("Successfully parsed OpenRouter response")
                    return parsed_result
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Raw content: {content}")
                    return self._fallback_response()
                    
        except Exception as e:
            print(f"OpenRouter request error: {e}")
            return self._fallback_response()
    
    def _fallback_response(self):
        """Fallback response when API fails"""
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
        if not ELEVENLABS_API_KEY:
            print("No ElevenLabs API key - voice cloning not available")
            return None
            
        try:
            voice = clone(
                name="User Voice",
                description="User's cloned voice",
                files=[audio_file_path]
            )
            self.user_voice_id = voice.voice_id
            print(f"Voice cloned successfully: {voice.voice_id}")
            return voice.voice_id
        except Exception as e:
            print(f"Voice cloning error: {e}")
            return None
    
    async def generate_speech(self, text: str, use_user_voice: bool = False) -> bytes:
        """Generate speech audio"""
        if not ELEVENLABS_API_KEY:
            print("No ElevenLabs API key - speech generation not available")
            return None
            
        try:
            if use_user_voice and self.user_voice_id:
                voice_id = self.user_voice_id
                print(f"Using user voice: {voice_id}")
            else:
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice
                print(f"Using default voice: {voice_id}")
            
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
            print("Audio generated successfully")
            return audio
        except Exception as e:
            print(f"Speech generation error: {e}")
            return None

# Initialize services
speech_to_text = SpeechToTextService()
speech_analysis = SpeechAnalysisService()
voice_service = VoiceService()