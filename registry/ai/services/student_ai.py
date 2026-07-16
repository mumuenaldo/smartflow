# registry/ai/services/student_ai.py
from ..ai_service import AIService
import json
import logging

logger = logging.getLogger(__name__)

class StudentAIService:
    """Phase 1: AI capabilities designed for student document enhancement"""
    
    def __init__(self):
        self.ai = AIService()
    
    def summarize_document(self, title: str, content: str) -> dict:
        """Generate AI summary of a document"""
        return self.ai.summarize_document(title, content)

    def check_grammar(self, content: str) -> dict:
        """Checks text for grammar, spelling, style, clarity, and calculates a writing score"""
        if not content or len(content) < 20:
            return {
                'score': 0, 'errors': [], 
                'suggestions': ['Document too short.'], 'overall_feedback': 'Provide more content.'
            }
        
        prompt = f"""Analyze this text for academic writing quality:
        \"\"\"{content[:4000]}\"\"\"
        
        Return a JSON object matching this structure:
        {{
            "score": 85,
            "errors": [
                {{"type": "grammar|spelling|style|clarity", "original": "text", "suggestion": "fix", "explanation": "why"}}
            ],
            "suggestions": ["overall structural suggestion"],
            "overall_feedback": "string text"
        }}"""
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt, config={{'response_mime_type': 'application/json'}}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Grammar check failed: {e}")
            return {'score': 0, 'errors': [], 'suggestions': [], 'overall_feedback': 'Error processing text.'}

    def get_improvement_suggestions(self, content: str) -> dict:
        """Provides actionable feedback to make paragraphs stronger or more academic"""
        prompt = f"""Provide deep academic improvements for this text:
        \"\"\"{content[:4000]}\"\"\"
        
        Return JSON format:
        {{
            "critical_weaknesses": ["list of weaknesses"],
            "actionable_fixes": [
                {{"original_passage": "context", "proposed_rewrite": "better version", "benefit": "why it is stronger"}}
            ]
        }}"""
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt, config={{'response_mime_type': 'application/json'}}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Improvement suggestions failed: {e}")
            return {'critical_weaknesses': [], 'actionable_fixes': []}

    def auto_tag_document(self, title: str, content: str) -> dict:
        """Categorizes document domains and extracts relevant academic keywords"""
        prompt = f"Analyze title: '{title}' and Content: '{content[:2000]}'. Return JSON: {{\"categories\": [\"Computer Science\", \"Thesis\"], \"keywords\": [\"AI\", \"Django\"]}}"
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt, config={{'response_mime_type': 'application/json'}}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Tagging failed: {e}")
            return {'categories': [], 'keywords': []}