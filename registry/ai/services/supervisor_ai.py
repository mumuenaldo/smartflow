# registry/ai/services/supervisor_ai.py
from ..ai_service import AIService
import json
import logging

logger = logging.getLogger(__name__)

class SupervisorAIService:
    """Phase 2: AI capabilities for supervisor evaluation workflows"""
    
    def __init__(self):
        self.ai = AIService()
    
    def generate_feedback_draft(self, title: str, content: str, criteria: str = "Standard academic assessment") -> dict:
        """Generate constructive feedback draft for a document"""
        if not content or len(content) < 50:
            return {
                'strengths': [],
                'weaknesses': [],
                'suggestions': ['Document is too short for meaningful feedback.'],
                'overall_assessment': 'Please provide a longer document.',
                'score': 0
            }
        
        prompt = f"""You are an experienced academic supervisor. Generate constructive, specific, and actionable feedback.
        
        Document Title: {title}
        Assessment Criteria: {criteria}
        
        Document Content:
        {content[:4000]}
        
        Return a JSON object with this exact structure:
        {{
            "strengths": ["Specific strength 1", "Specific strength 2", "Specific strength 3"],
            "weaknesses": ["Specific area 1", "Specific area 2", "Specific area 3"],
            "suggestions": ["Actionable suggestion 1", "Actionable suggestion 2", "Actionable suggestion 3"],
            "overall_assessment": "2-3 sentence overall assessment",
            "score": 75
        }}
        
        Return ONLY the JSON, no other text."""
        
        try:
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Feedback gen failed: {e}")
            return {
                'strengths': ['AI service temporarily unavailable.'],
                'weaknesses': [],
                'suggestions': ['Please try again later.'],
                'overall_assessment': 'Unable to generate feedback at this time.',
                'score': 0
            }
    
    def analyze_large_report(self, content: str) -> dict:
        """Extract key sections from a large report"""
        if not content or len(content) < 100:
            return {
                'executive_summary': 'Document is too short to analyze.',
                'key_findings': [],
                'methodology': '',
                'conclusions': '',
                'recommendations': []
            }
        
        prompt = f"""You are a research analyst. Extract key sections from this report.
        
        Report Content:
        {content[:5000]}
        
        Return a JSON object with this exact structure:
        {{
            "executive_summary": "2-3 sentence summary of the entire report",
            "key_findings": ["Finding 1", "Finding 2", "Finding 3", "Finding 4"],
            "methodology": "Brief description of the methodology used",
            "conclusions": "Main conclusions drawn from the report",
            "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
        }}
        
        Return ONLY the JSON, no other text."""
        
        try:
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Report analysis failed: {e}")
            return {
                'executive_summary': 'Unable to analyze report.',
                'key_findings': [],
                'methodology': '',
                'conclusions': '',
                'recommendations': []
            }
    
    def detect_document_risks(self, content: str) -> dict:
        """Detect potential risks in a document"""
        if not content or len(content) < 50:
            return {
                'risks': [],
                'overall_risk_level': 'low',
                'critical_issues': ['Document is too short to analyze.']
            }
        
        prompt = f"""You are a quality assurance expert. Analyze this document for potential risks and issues.
        
        Document Content:
        {content[:4000]}
        
        Return a JSON object with this exact structure:
        {{
            "risks": [
                {{
                    "type": "reference|plagiarism|incomplete|factual|methodological",
                    "description": "Detailed description of the issue",
                    "severity": "high|medium|low",
                    "suggestion": "Specific suggestion to fix this issue"
                }}
            ],
            "overall_risk_level": "high|medium|low",
            "critical_issues": ["Issue 1", "Issue 2"]
        }}
        
        Return ONLY the JSON, no other text."""
        
        try:
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Risk detection failed: {e}")
            return {
                'risks': [],
                'overall_risk_level': 'unknown',
                'critical_issues': ['Unable to analyze risks.']
            }