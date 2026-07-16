# registry/ai/services/staff_ai.py
from ..ai_service import AIService
import json
import logging

logger = logging.getLogger(__name__)

class StaffAIService:
    """Phase 2: AI capabilities for staff workflow optimization"""
    
    def __init__(self):
        self.ai = AIService()
    
    def predict_workload(self, documents_data: list) -> dict:
        """Predict workload based on document patterns"""
        try:
            prompt = f"""You are a workflow analyst. Analyze this document submission data and predict workload.
            
            Document Data: {json.dumps(documents_data[:20]) if documents_data else 'No data provided.'}
            
            Return a JSON object with:
            {{
                "predicted_submissions_today": 15,
                "busy_periods": ["10:00 AM - 12:00 PM", "2:00 PM - 4:00 PM"],
                "recommended_staff_allocation": 3,
                "bottleneck_risk": "medium"
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Workload prediction failed: {e}")
            return {
                'predicted_submissions_today': 0,
                'busy_periods': [],
                'recommended_staff_allocation': 1,
                'bottleneck_risk': 'unknown'
            }
    
    def suggest_routing(self, document_title: str, document_content: str, available_supervisors: list) -> dict:
        """Suggest which supervisor to route a document to"""
        try:
            prompt = f"""You are a document routing expert. Suggest the best supervisor for this document.
            
            Document Title: {document_title}
            Document Content: {document_content[:1000]}
            
            Available Supervisors: {json.dumps(available_supervisors) if available_supervisors else 'No supervisors available.'}
            
            Return a JSON object with:
            {{
                "recommended_supervisor": "Supervisor Name",
                "reason": "Why this supervisor is the best fit",
                "confidence": 85,
                "alternatives": ["Alternative 1", "Alternative 2"]
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Routing suggestion failed: {e}")
            return {
                'recommended_supervisor': 'Unassigned',
                'reason': 'Unable to suggest routing.',
                'confidence': 0,
                'alternatives': []
            }
    
    def check_duplicate(self, title: str, content: str, existing_documents: list) -> dict:
        """Check if a document might be a duplicate"""
        try:
            prompt = f"""You are a duplicate detection expert. Check if this document is likely a duplicate.
            
            New Document Title: {title}
            New Document Content: {content[:1000]}
            
            Existing Documents: {json.dumps(existing_documents[:10]) if existing_documents else 'No existing documents provided.'}
            
            Return a JSON object with:
            {{
                "is_duplicate": false,
                "confidence": 75,
                "potential_matches": [
                    {{"id": "DOC-123", "title": "Similar Document Title", "similarity_score": 85}}
                ],
                "reason": "Explanation of the duplicate check"
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return {
                'is_duplicate': False,
                'confidence': 0,
                'potential_matches': [],
                'reason': 'Unable to check for duplicates.'
            }
    
    def estimate_processing_time(self, document_type: str, content_length: int) -> dict:
        """Estimate how long processing a document will take"""
        try:
            prompt = f"""You are a time estimation expert. Estimate processing time for this document.
            
            Document Type: {document_type}
            Content Length: {content_length} words
            
            Return a JSON object with:
            {{
                "estimated_minutes": 30,
                "estimated_hours": 0.5,
                "complexity": "medium",
                "factors": ["Factor 1 affecting time", "Factor 2"],
                "confidence": 80
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Time estimation failed: {e}")
            return {
                'estimated_minutes': 30,
                'estimated_hours': 0.5,
                'complexity': 'medium',
                'factors': [],
                'confidence': 50
            }