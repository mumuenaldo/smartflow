# registry/ai/ai_service.py
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class AIService:
    """Core AI Service using Google Gemini API (FREE!)"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file!")
        
        # Import and initialize the NEW google-genai client
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.model = "gemini-2.5-flash"
            print("✅ Gemini AI Service initialized!")
        except ImportError:
            raise ImportError("Please install google-genai: pip install google-genai")
    
    def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"Error: {str(e)}"
    
    def generate_json(self, prompt: str) -> dict:
        """Generate JSON response from Gemini"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"JSON generation error: {e}")
            return {}
    
    def summarize_document(self, title: str, content: str) -> dict:
        """Summarize a document using Gemini"""
        if not content or len(content) < 50:
            return {
                'summary': 'Document is too short to summarize.',
                'key_points': [],
                'word_count': len(content.split()),
                'reading_time_minutes': 1
            }
        
        prompt = f"""You are an expert document summarizer. Create a clear, concise summary.
        
        Title: {title}
        
        Content:
        {content[:3000]}
        
        Format your response as JSON with exactly these keys:
        {{
            "summary": "A 2-3 sentence overview",
            "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"]
        }}
        
        Return ONLY the JSON, no other text."""
        
        result = self.generate_json(prompt)
        if result:
            # Add metadata
            word_count = len(content.split())
            result['word_count'] = word_count
            result['reading_time_minutes'] = max(1, round(word_count / 200))
            return result
        
        return {
            'summary': 'Unable to generate summary.',
            'key_points': [],
            'word_count': len(content.split()),
            'reading_time_minutes': 1
        }
    
    def test_connection(self) -> bool:
        """Test if Gemini is working"""
        try:
            response = self.generate_text("Say 'Hello SmartFlow!'")
            return "Hello SmartFlow" in response
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False