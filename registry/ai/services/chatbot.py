# registry/ai/services/chatbot.py
from ..ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class SmartflowChatbot:
    """Phase 4: Multi-turn contextual user interface assistant"""
    
    def __init__(self):
        self.ai = AIService()

    def generate_response(self, user_message: str, chat_history: list, context_metadata: str = "") -> str:
        """Engages in dialogue regarding status lookups or workflow tutorials"""
        system_instruction = (
            "You are Smartflow's direct companion assistant. You clarify document queues, statuses, "
            "and general operations. Use clear, helpful language. Keep answers concise."
        )
        
        # Structure payload to feed previous lines alongside target user message
        formatted_contents = []
        if context_metadata:
            formatted_contents.append(f"[System Environment Context]: {context_metadata}")
            
        for Turn in chat_history:
            formatted_contents.append(f"{Turn['sender']}: {Turn['text']}")
            
        formatted_contents.append(f"User: {user_message}")

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents="\n".join(formatted_contents),
                config={{'system_instruction': system_instruction}}
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Chatbot failed to respond: {e}")
            return "I am having trouble answering right now. Please check your submission pipeline dashboard."