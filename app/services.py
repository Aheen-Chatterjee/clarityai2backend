import httpx
import json
import tempfile
import os
import requests
from gtts import gTTS
import io
from app.config import OPENROUTER_API_KEY

print(f"OpenRouter API Key configured: {bool(OPENROUTER_API_KEY)}")

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
                    "speech": "Rewritten speech for this demographic, considering what they care about. Match original speech length."
                }},
                {{
                    "demographic": "Second demographic", 
                    "speech": "Rewritten speech for this demographic in 2-3 sentences, considering what they care about. Match original speech length."
                }},
                {{
                    "demographic": "Third demographic",
                    "speech": "Rewritten speech for this demographic in 2-3 sentences, considering what they care about. Match original speech length."
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
        self.voices = {
            'male': 'co.uk',     # British male
            'female': 'ca',      # Canadian female  
            'user': 'com.au'     # Australian (as "user" voice)
        }
        self.current_voice = 'male'
    
    async def clone_voice(self, audio_file_path: str) -> str:
        """Simulate voice cloning by switching to user voice"""
        try:
            # Since we can't actually clone, just mark as user voice available
            self.current_voice = 'user'
            print("Voice 'cloned' successfully (using different accent)")
            return "user_voice_id_simulation"
        except Exception as e:
            print(f"Voice simulation error: {e}")
            return None
    
    async def generate_speech(self, text: str, use_user_voice: bool = False) -> bytes:
        """Generate speech using Google Text-to-Speech"""
        try:
            # Choose voice based on user preference
            if use_user_voice and self.current_voice == 'user':
                tld = self.voices['user']
                print("Using 'user' voice (Australian accent)")
            else:
                tld = self.voices['male']
                print("Using default voice (British accent)")
            
            # Generate speech with gTTS
            tts = gTTS(text=text, lang='en', tld=tld, slow=False)
            
            # Save to bytes
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            audio_data = mp3_fp.read()
            print(f"Audio generated successfully: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            print(f"Speech generation error: {e}")
            return None

# Initialize services
speech_analysis = SpeechAnalysisService()
voice_service = VoiceService()