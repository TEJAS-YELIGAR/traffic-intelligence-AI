"""
Prediction Service - Business logic for risk predictions.
Separates business logic from Flask routes.
"""
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
import numpy as np

from services.logger import setup_logger
from services.model_loader import get_model
from services.validators import validate_predict_request, ValidationError
from services.feature_transformer import transform_predict_input
from services.geo_service import get_geo_service

logger = setup_logger(__name__)

class PredictionService:
    """
    Service for handling prediction business logic.
    """
    
    def __init__(self):
        """Initialize prediction service."""
        self.model = None
        self.geo_service = get_geo_service()
        self._load_model()
    
    def _load_model(self):
        """Load model on initialization."""
        try:
            self.model = get_model()
            logger.info("Prediction service initialized")
        except Exception as e:
            logger.error(f"Failed to load model in prediction service: {e}")
            self.model = None
    
    def predict(self, data: Dict) -> Tuple[Dict, float]:
        """
        Make risk prediction with performance timing.
        
        Args:
            data: Input features dictionary
            
        Returns:
            Tuple of (prediction_result, processing_time_ms)
            
        Raises:
            ValidationError: If input validation fails
            RuntimeError: If model is not available
        """
        start_time = time.time()
        
        # Validate input
        validated_data = validate_predict_request(data)
        
        # Engineer geo-features
        latitude = validated_data.get('latitude', 0.0)
        longitude = validated_data.get('longitude', 0.0)
        geo_features = self.geo_service.engineer_geo_features(latitude, longitude)
        
        # Transform input
        input_df = transform_predict_input(validated_data)
        
        # Check model
        if self.model is None:
            raise RuntimeError("Model not available")
        
        # Make prediction
        try:
            probabilities = self.model.predict_proba(input_df)[0]
            predicted_class = self.model.predict(input_df)[0]
            
            # Get probability
            if len(probabilities) == 2:
                probability = float(probabilities[1])
            else:
                probability = float(max(probabilities))
            
            severity = int(predicted_class)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Store prediction
            self.geo_service.store_prediction(
                latitude, longitude, probability, severity,
                validated_data, geo_features
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(probability)
            
            result = {
                "probability": probability,
                "severity": severity,
                "risk_level": risk_level,
                "geo_features": geo_features,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(
                f"Prediction: prob={probability:.3f}, severity={severity}, "
                f"time={processing_time:.2f}ms"
            )
            
            return result, processing_time
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise RuntimeError(f"Prediction error: {str(e)}")
    
    def _determine_risk_level(self, probability: float) -> str:
        """
        Determine risk level from probability.
        
        Args:
            probability: Risk probability (0-1)
            
        Returns:
            Risk level string
        """
        if probability >= 0.7:
            return "HIGH"
        elif probability >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_model_confidence(self) -> Optional[float]:
        """
        Get model confidence indicator.
        
        Returns:
            Confidence score (0-1) or None if unavailable
        """
        if self.model is None:
            return None
        
        # Simple confidence based on model availability
        # In production, this could use prediction variance, ensemble agreement, etc.
        return 0.85  # Placeholder

# Global instance
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """Get global prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
