"""
AI Risk Assistant Chatbot Service
Conversational chatbot with natural language understanding and context awareness.
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from services.logger import setup_logger
from services.prediction_service import get_prediction_service
from services.forecasting_service import get_forecasting_service
from services.geo_service import get_geo_service
from services.anomaly_service import get_anomaly_service

logger = setup_logger(__name__)

class ChatService:
    """
    Conversational chatbot service with context awareness and natural responses.
    """
    
    def __init__(self):
        """Initialize chat service with dependencies."""
        self.prediction_service = get_prediction_service()
        self.forecasting_service = get_forecasting_service()
        self.geo_service = get_geo_service()
        self.anomaly_service = get_anomaly_service()
        
        # Conversation context per user
        self.conversations = {}
        
        # Initialize patterns
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize NLP patterns for entity extraction."""
        self.weather_patterns = {
            r'\brain\b|\brainy\b|\braining\b': 'Rain',
            r'\bsnow\b|\bsnowy\b|\bsnowing\b': 'Snow',
            r'\bfog\b|\bfoggy\b': 'Fog',
            r'\bcloud\b|\bcloudy\b|\bclouds\b': 'Cloudy',
            r'\bclear\b|\bsunny\b|\bsun\b': 'Clear',
            r'\bstorm\b|\bstormy\b': 'Rain'
        }
        
        self.time_patterns = [
            (r'(\d+)\s*(am|pm)', self._parse_12h),
            (r'(\d+):(\d+)\s*(am|pm)', self._parse_12h_colon),
            (r"(\d+)\s*o'?clock", lambda m: int(m.group(1))),
            (r'\bmorning\b', 8),
            (r'\bafternoon\b', 14),
            (r'\bevening\b', 18),
            (r'\bnight\b|\blate\b', 22),
            (r'\bnoon\b|\bmidday\b', 12)
        ]
    
    def _parse_12h(self, match):
        """Parse 12-hour time format."""
        hour = int(match.group(1))
        period = match.group(2).lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return hour
    
    def _parse_12h_colon(self, match):
        """Parse 12-hour time with colon."""
        hour = int(match.group(1))
        period = match.group(3).lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return hour
    
    def get_conversation(self, user_id: str) -> Dict:
        """Get or create conversation context for user."""
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                'entities': {},
                'last_intent': None,
                'last_prediction': None,
                'message_count': 0
            }
        return self.conversations[user_id]
    
    def extract_entities(self, message: str) -> Dict:
        """Extract entities from natural language with context awareness."""
        entities = {}
        msg_lower = message.lower()
        
        # Extract weather
        for pattern, value in self.weather_patterns.items():
            if re.search(pattern, msg_lower):
                entities['weather'] = value
                break
        
        # Extract numeric values with context
        # Wind speed
        wind_match = re.search(r'wind.*?(\d+)|(\d+).*?wind|windy', msg_lower)
        if wind_match:
            entities['wind_speed'] = float(wind_match.group(1) or wind_match.group(2) or 15)
        
        # Visibility
        vis_match = re.search(r'visibility.*?(\d+)|(\d+).*?mile|low.*?visibility|poor.*?visibility', msg_lower)
        if vis_match:
            entities['visibility'] = float(vis_match.group(1) or vis_match.group(2) or 2.0)
        elif 'low visibility' in msg_lower or 'poor visibility' in msg_lower:
            entities['visibility'] = 2.0
        
        # Temperature
        temp_match = re.search(r'temp.*?(\d+)|(\d+).*?degree|hot|warm|cold|cool', msg_lower)
        if temp_match:
            entities['temperature'] = float(temp_match.group(1) or temp_match.group(2) or 70)
        elif 'hot' in msg_lower or 'warm' in msg_lower:
            entities['temperature'] = 80.0
        elif 'cold' in msg_lower or 'cool' in msg_lower:
            entities['temperature'] = 50.0
        
        # Traffic
        if re.search(r'heavy.*?traffic|busy|congested', msg_lower):
            entities['traffic_density'] = 85.0
        elif re.search(r'moderate.*?traffic|normal.*?traffic', msg_lower):
            entities['traffic_density'] = 50.0
        elif re.search(r'light.*?traffic|low.*?traffic', msg_lower):
            entities['traffic_density'] = 25.0
        else:
            traffic_match = re.search(r'traffic.*?(\d+)|(\d+).*?traffic', msg_lower)
            if traffic_match:
                entities['traffic_density'] = float(traffic_match.group(1) or traffic_match.group(2))
        
        # Time
        for pattern in self.time_patterns:
            if isinstance(pattern, tuple):
                match = re.search(pattern[0], msg_lower)
                if match:
                    entities['hour'] = pattern[1](match) if callable(pattern[1]) else pattern[1]
                    break
        
        # Location
        lat_match = re.search(r'lat.*?(-?\d+\.?\d*)|latitude.*?(-?\d+\.?\d*)', msg_lower)
        lon_match = re.search(r'lon.*?(-?\d+\.?\d*)|longitude.*?(-?\d+\.?\d*)', msg_lower)
        if lat_match:
            entities['latitude'] = float(lat_match.group(1) or lat_match.group(2))
        if lon_match:
            entities['longitude'] = float(lon_match.group(1) or lon_match.group(2))
        
        return entities
    
    def detect_intent(self, message: str, context: Dict) -> str:
        """Detect user intent with context awareness."""
        msg_lower = message.lower()
        
        # Greeting
        if re.search(r'\b(hi|hello|hey|greetings)\b', msg_lower):
            return 'greeting'
        
        # Question patterns
        if re.search(r'\b(what|how|why|when|where|tell me|explain|describe)\b', msg_lower):
            if re.search(r'\b(risk|danger|safe|accident)\b', msg_lower):
                return 'ask_risk'
            elif re.search(r'\b(forecast|future|next|prediction)\b', msg_lower):
                return 'ask_forecast'
            elif re.search(r'\b(important|factor|feature|matter)\b', msg_lower):
                return 'ask_importance'
            elif re.search(r'\b(high|dangerous|risk.*?area|cluster)\b', msg_lower):
                return 'ask_areas'
            else:
                return 'ask_general'
        
        # Command patterns
        if re.search(r'\b(predict|check|calculate|assess|evaluate).*?risk\b', msg_lower):
            return 'predict'
        if re.search(r'\b(forecast|predict.*?future|next.*?24|24.*?hour)\b', msg_lower):
            return 'forecast'
        if re.search(r'\b(clear|reset|remove|clean).*?map\b', msg_lower):
            return 'clear_map'
        if re.search(r'\b(help|commands|what.*?can.*?do|how.*?use)\b', msg_lower):
            return 'help'
        
        # Follow-up questions
        if context.get('last_prediction'):
            if re.search(r'\b(why|reason|cause|because|factor)\b', msg_lower):
                return 'explain_prediction'
            if re.search(r'\b(how.*?high|how.*?low|what.*?level)\b', msg_lower):
                return 'ask_level'
        
        # Default: try to extract entities and predict
        entities = self.extract_entities(message)
        if len(entities) > 0:
            return 'predict'
        
        return 'unknown'
    
    def generate_response(self, intent: str, message: str, context: Dict) -> Dict:
        """Generate natural conversational response."""
        context['message_count'] = context.get('message_count', 0) + 1
        
        # Merge new entities with context
        new_entities = self.extract_entities(message)
        context['entities'].update(new_entities)
        entities = context['entities']
        
        # Default values
        defaults = {
            'weather': 1,
            'visibility': 10.0,
            'temperature': 70.0,
            'wind_speed': 5.0,
            'hour': datetime.now().hour,
            'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
            'traffic_density': 50.0,
            'latitude': 34.0522,
            'longitude': -118.2437
        }
        
        for key, val in defaults.items():
            if key not in entities:
                entities[key] = val
        
        # Map weather
        weather_map = {'Clear': 0, 'Cloudy': 1, 'Rain': 2, 'Snow': 3, 'Fog': 4}
        if isinstance(entities.get('weather'), str):
            entities['weather'] = weather_map.get(entities['weather'], 1)
        
        reply = ""
        action = "none"
        structured_data = {}
        
        if intent == 'greeting':
            reply = "Hello! I'm your AI Risk Assistant. I can help you predict traffic accident risk, get forecasts, and understand risk factors. What would you like to know?"
            action = "none"
        
        elif intent == 'predict' or intent == 'ask_risk':
            # Check if we have enough info
            required = ['weather', 'visibility', 'temperature', 'wind_speed', 'hour', 'traffic_density']
            missing = [f for f in required if f not in entities or entities[f] is None]
            
            if len(missing) > 2 and context['message_count'] == 1:
                reply = f"I'd be happy to predict the risk! I need a bit more information. Could you tell me about the weather conditions, traffic level, and time of day?"
                action = "none"
            else:
                try:
                    result, _ = self.prediction_service.predict(entities)
                    prob = result['probability']
                    severity = result['severity']
                    risk_level = result['risk_level']
                    
                    context['last_prediction'] = result
                    context['last_intent'] = 'predict'
                    
                    # Natural language response
                    if risk_level == 'HIGH':
                        reply = f"⚠️ The risk assessment shows a **HIGH** risk level with {prob*100:.1f}% probability. "
                    elif risk_level == 'MEDIUM':
                        reply = f"⚠️ The risk is **MODERATE** at {prob*100:.1f}% probability. "
                    else:
                        reply = f"✅ The risk is **LOW** at {prob*100:.1f}% probability. "
                    
                    reply += f"The predicted severity level is {severity}. "
                    
                    # Add contextual factors
                    factors = []
                    if entities.get('weather') == 2:
                        factors.append("rainy weather")
                    if entities.get('visibility', 10) < 5:
                        factors.append("low visibility")
                    if entities.get('traffic_density', 50) > 70:
                        factors.append("heavy traffic")
                    if entities.get('hour') in [7, 8, 9, 17, 18, 19]:
                        factors.append("rush hour timing")
                    
                    if factors:
                        reply += f"Key factors contributing to this risk include: {', '.join(factors)}. "
                    
                    reply += "Would you like me to explain any of these factors in more detail?"
                    
                    action = "predict"
                    structured_data = {
                        'probability': prob,
                        'severity': severity,
                        'risk_level': risk_level,
                        'entities': entities,
                        'geo_features': result.get('geo_features', {})
                    }
                except Exception as e:
                    logger.error(f"Prediction failed: {e}", exc_info=True)
                    reply = "I'm having trouble making that prediction right now. Could you try rephrasing your request?"
                    action = "none"
        
        elif intent == 'forecast' or intent == 'ask_forecast':
            try:
                forecast = self.forecasting_service.forecast_24h()
                peak = forecast.get('peak_hour', 18)
                confidence = forecast.get('confidence_score', 0.5)
                
                reply = f"📊 Based on recent patterns, the 24-hour forecast shows peak risk around {peak}:00. "
                reply += f"The forecast confidence is {confidence*100:.0f}%. "
                reply += "Generally, higher risk is expected during morning rush hours (7-9 AM) and evening rush hours (5-7 PM). "
                reply += "Would you like more details about specific hours?"
                
                action = "forecast"
                structured_data = forecast
            except Exception as e:
                logger.error(f"Forecast failed: {e}", exc_info=True)
                reply = "I couldn't generate a forecast right now. Please try again in a moment."
                action = "none"
        
        elif intent == 'explain_prediction' or intent == 'ask_general':
            if context.get('last_prediction'):
                pred = context['last_prediction']
                reply = f"Let me explain the risk calculation. The system considers several factors:\n\n"
                reply += f"• **Weather conditions**: Rain, fog, and snow increase risk\n"
                reply += f"• **Visibility**: Lower visibility means higher risk\n"
                reply += f"• **Traffic density**: Heavy traffic increases accident probability\n"
                reply += f"• **Time of day**: Rush hours (7-9 AM, 5-7 PM) are riskier\n"
                reply += f"• **Location factors**: Distance to highways and urban density matter\n\n"
                reply += f"For your recent prediction, the risk was {pred['probability']*100:.1f}% ({pred['risk_level']} level). "
                reply += "Would you like to know which specific factors contributed most?"
            else:
                reply = "I'd be happy to explain! Risk is calculated based on weather conditions, visibility, traffic density, time of day, and location factors. "
                reply += "Would you like me to make a prediction first so I can explain the specific factors?"
            action = "explain"
        
        elif intent == 'ask_importance':
            reply = "The most important factors for risk prediction are:\n\n"
            reply += "1. **Visibility** (25%) - Lower visibility significantly increases risk\n"
            reply += "2. **Temperature** (20%) - Extreme temperatures affect road conditions\n"
            reply += "3. **Time of day** (15%) - Rush hours have higher accident rates\n"
            reply += "4. **Traffic density** (15%) - More traffic means more potential accidents\n"
            reply += "5. **Weather** (10%) - Rain, fog, and snow increase risk\n"
            reply += "6. **Wind speed** (10%) - Strong winds can affect vehicle control\n"
            reply += "7. **Location** (5%) - Urban density and highway proximity matter\n\n"
            reply += "You can see the detailed feature importance chart on the dashboard!"
            action = "feature_importance"
        
        elif intent == 'ask_areas':
            try:
                clusters = self.geo_service.get_risk_clusters(n_clusters=5)
                if clusters:
                    reply = f"I've identified {len(clusters)} high-risk areas:\n\n"
                    for i, c in enumerate(clusters[:3], 1):
                        reply += f"{i}. Area with {c['average_risk']*100:.1f}% average risk ({c['count']} predictions)\n"
                    reply += "\nThese areas show consistently higher risk patterns. Would you like me to show them on the map?"
                else:
                    reply = "I don't have enough data to identify high-risk clusters yet. Make some predictions and I'll be able to identify patterns!"
                action = "high_risk_areas"
                structured_data = {'clusters': clusters}
            except Exception as e:
                logger.error(f"Failed to get clusters: {e}", exc_info=True)
                reply = "I'm having trouble retrieving risk areas right now."
                action = "none"
        
        elif intent == 'clear_map':
            reply = "I've cleared the map for you. All markers and heatmap data have been removed."
            action = "clear_map"
        
        elif intent == 'help':
            reply = "I can help you with:\n\n"
            reply += "🔹 **Risk Predictions**: Ask me about risk with specific conditions\n"
            reply += "🔹 **Forecasts**: Get 24-hour risk forecasts\n"
            reply += "🔹 **Explanations**: Understand why risk is high or low\n"
            reply += "🔹 **High-Risk Areas**: Find dangerous locations\n"
            reply += "🔹 **Feature Importance**: Learn which factors matter most\n\n"
            reply += "Just talk to me naturally! For example:\n"
            reply += "• 'What's the risk with rainy weather and heavy traffic?'\n"
            reply += "• 'Forecast the next 24 hours'\n"
            reply += "• 'Why is the risk high?'\n"
            action = "help"
        
        elif intent == 'unknown':
            reply = "I'm not quite sure what you're asking. I can help with:\n"
            reply += "• Risk predictions\n"
            reply += "• Forecasts\n"
            reply += "• Risk explanations\n"
            reply += "• High-risk areas\n\n"
            reply += "Try asking something like 'What's the risk with [conditions]?' or say 'help' for more options."
            action = "none"
        
        return {
            'reply': reply,
            'action': action,
            'structured_data': structured_data
        }
    
    def process_message(self, message: str, user_id: str = "default") -> Dict:
        """Process user message and generate conversational response."""
        logger.info(f"Processing message: {message[:50]}...")
        
        context = self.get_conversation(user_id)
        intent = self.detect_intent(message, context)
        
        response = self.generate_response(intent, message, context)
        
        return response

# Global instance
_chat_service = None

def get_chat_service() -> ChatService:
    """Get global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
