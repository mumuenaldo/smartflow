# registry/ai/services/admin_ai.py
from ..ai_service import AIService
import json
import logging

logger = logging.getLogger(__name__)

class AdminAIService:
    """Phase 3: AI capabilities for system administration and analytics"""
    
    def __init__(self):
        self.ai = AIService()
    
    def generate_system_analytics(self, data: dict) -> dict:
        """Generate comprehensive system analytics from data"""
        try:
            prompt = f"""You are a system analytics expert. Analyze this data and generate insights.
            
            System Data: {json.dumps(data) if data else 'No data provided.'}
            
            Return a JSON object with:
            {{
                "system_health": "good",
                "bottlenecks": [{{"area": "Department name", "issue": "Description", "impact": "high", "recommendation": "How to fix"}}],
                "trends": [{{"metric": "Submissions", "direction": "increasing", "percentage_change": 15}}],
                "optimization_suggestions": ["Suggestion 1", "Suggestion 2"],
                "predicted_next_month_submissions": 150
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"System analytics failed: {e}")
            return {
                'system_health': 'unknown',
                'bottlenecks': [],
                'trends': [],
                'optimization_suggestions': [],
                'predicted_next_month_submissions': 0
            }
    
    def detect_anomalies(self, audit_data: dict) -> dict:
        """Detect anomalous patterns in system activity"""
        try:
            prompt = f"""You are a security analyst. Detect anomalies in this system activity data.
            
            Audit Data: {json.dumps(audit_data) if audit_data else 'No data provided.'}
            
            Return a JSON object with:
            {{
                "anomalies": [
                    {{"type": "unusual_activity", "description": "Description", "severity": "medium", "users_involved": ["user1"], "recommendation": "What to do"}}
                ],
                "risk_score": 65,
                "alert_level": "yellow",
                "actions_recommended": ["Action 1", "Action 2"]
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                'anomalies': [],
                'risk_score': 0,
                'alert_level': 'green',
                'actions_recommended': []
            }
    
    def predict_trends(self, historical_data: dict) -> dict:
        """Predict future trends based on historical data"""
        try:
            prompt = f"""You are a trend prediction expert. Analyze this historical data and predict future trends.
            
            Historical Data: {json.dumps(historical_data) if historical_data else 'No data provided.'}
            
            Return a JSON object with:
            {{
                "predicted_trends": [
                    {{"metric": "Document Submissions", "predicted_value": 150, "confidence_interval": [135, 165], "drivers": ["Seasonal increase"]}}
                ],
                "peak_periods": ["January", "May", "October"],
                "recommended_capacity": 5,
                "actionable_insights": ["Insight 1", "Insight 2"]
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Trend prediction failed: {e}")
            return {
                'predicted_trends': [],
                'peak_periods': [],
                'recommended_capacity': 1,
                'actionable_insights': []
            }
    
    def generate_performance_report(self, department_data: dict) -> dict:
        """Generate performance report for departments"""
        try:
            prompt = f"""You are a performance analyst. Generate a performance report for departments.
            
            Department Data: {json.dumps(department_data) if department_data else 'No data provided.'}
            
            Return a JSON object with:
            {{
                "top_performers": ["Dept 1", "Dept 2"],
                "underperformers": ["Dept 3"],
                "average_processing_time": 2.5,
                "performance_score": 78,
                "recommendations": [{{"department": "Dept Name", "issue": "Issue description", "suggestion": "Improvement suggestion"}}],
                "overall_rating": "good"
            }}
            
            Return ONLY the JSON."""
            return self.ai.generate_json(prompt)
        except Exception as e:
            logger.error(f"Performance report failed: {e}")
            return {
                'top_performers': [],
                'underperformers': [],
                'average_processing_time': 0,
                'performance_score': 0,
                'recommendations': [],
                'overall_rating': 'unknown'
            }