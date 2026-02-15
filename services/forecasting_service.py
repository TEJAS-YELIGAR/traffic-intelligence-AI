"""
Intelligent Time-Series Forecasting Service
Uses historical predictions with seasonality for accurate forecasting.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from services.logger import setup_logger
from services.geo_service import get_geo_service

logger = setup_logger(__name__)

class ForecastingService:
    """
    Advanced time-series forecasting service with seasonality.
    """
    
    def __init__(self):
        """Initialize forecasting service."""
        self.geo_service = get_geo_service()
        self.forecaster = None
        self._train_forecaster()
    
    def _train_forecaster(self):
        """Train GradientBoosting regressor for forecasting."""
        try:
            # Load historical data
            historical = self.geo_service.get_historical_clusters(hours=168)  # 7 days
            
            if len(historical) < 24:
                logger.warning("Insufficient historical data for forecaster training")
                self.forecaster = None
                return
            
            # Prepare training data
            df = pd.DataFrame(historical)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            # Features: hour, day_of_week, is_weekend, rolling averages
            df = df.sort_values('timestamp')
            df['rolling_3h'] = df['probability'].rolling(window=3, min_periods=1).mean()
            df['rolling_24h'] = df['probability'].rolling(window=24, min_periods=1).mean()
            
            # Prepare features and target
            X = df[['hour', 'day_of_week', 'is_weekend', 'rolling_3h', 'rolling_24h']].fillna(0)
            y = df['probability'].values
            
            # Train model
            self.forecaster = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.forecaster.fit(X, y)
            
            logger.info("Forecaster trained successfully")
        
        except Exception as e:
            logger.warning(f"Forecaster training failed: {e}")
            self.forecaster = None
    
    def forecast_24h(self) -> Dict:
        """
        Generate 24-hour forecast with seasonality.
        
        Returns:
            Dictionary with hourly_forecast, peak_hour, confidence_score
        """
        try:
            # Get recent history for rolling averages
            historical = self.geo_service.get_historical_clusters(hours=24)
            
            if len(historical) < 3:
                # Fallback to simple forecast
                return self._simple_forecast()
            
            df = pd.DataFrame(historical)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate current rolling averages
            recent_3h = df['probability'].tail(3).mean() if len(df) >= 3 else df['probability'].mean()
            recent_24h = df['probability'].mean()
            
            current_time = datetime.now()
            current_hour = current_time.hour
            current_day = current_time.weekday()
            is_weekend = 1 if current_day >= 5 else 0
            
            hourly_forecast = []
            peak_hour = current_hour
            max_risk = 0.0
            
            if self.forecaster is not None:
                # Use trained model
                for h in range(24):
                    hour = (current_hour + h) % 24
                    day_of_week = (current_day + (h // 24)) % 7
                    is_weekend_hour = 1 if day_of_week >= 5 else 0
                    
                    # Update rolling averages (simplified)
                    rolling_3h = recent_3h * (1 - 0.1)  # Decay
                    rolling_24h = recent_24h
                    
                    features = np.array([[
                        hour,
                        day_of_week,
                        is_weekend_hour,
                        rolling_3h,
                        rolling_24h
                    ]])
                    
                    predicted_risk = self.forecaster.predict(features)[0]
                    predicted_risk = np.clip(predicted_risk, 0.0, 1.0)
                    
                    hourly_forecast.append({
                        'hour': hour,
                        'risk': float(predicted_risk),
                        'timestamp': (current_time + timedelta(hours=h)).isoformat()
                    })
                    
                    if predicted_risk > max_risk:
                        max_risk = predicted_risk
                        peak_hour = hour
            else:
                # Simple forecast with seasonality
                return self._seasonal_forecast(current_hour, current_day, recent_24h)
            
            # Calculate confidence (based on data availability and model)
            confidence_score = min(1.0, len(historical) / 100.0)
            
            return {
                'hourly_forecast': hourly_forecast,
                'peak_hour': int(peak_hour),
                'confidence_score': float(confidence_score),
                'status': 'success'
            }
        
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}", exc_info=True)
            return self._simple_forecast()
    
    def _seasonal_forecast(self, current_hour: int, current_day: int, 
                          baseline: float) -> Dict:
        """
        Generate seasonal forecast using hour-of-day and day-of-week patterns.
        
        Args:
            current_hour: Current hour (0-23)
            current_day: Current day of week (0-6)
            baseline: Baseline risk level
            
        Returns:
            Forecast dictionary
        """
        # Hourly pattern (rush hours have higher risk)
        hour_pattern = {
            h: 1.2 if h in [7, 8, 9, 17, 18, 19] else  # Rush hours
            0.8 if h in [22, 23, 0, 1, 2, 3, 4] else  # Late night
            1.0  # Normal hours
            for h in range(24)
        }
        
        # Day of week pattern (weekends different)
        is_weekend = 1 if current_day >= 5 else 0
        day_factor = 1.1 if is_weekend else 1.0
        
        hourly_forecast = []
        peak_hour = current_hour
        max_risk = 0.0
        
        for h in range(24):
            hour = (current_hour + h) % 24
            risk = baseline * hour_pattern[hour] * day_factor
            risk = np.clip(risk, 0.0, 1.0)
            
            hourly_forecast.append({
                'hour': hour,
                'risk': float(risk),
                'timestamp': (datetime.now() + timedelta(hours=h)).isoformat()
            })
            
            if risk > max_risk:
                max_risk = risk
                peak_hour = hour
        
        return {
            'hourly_forecast': hourly_forecast,
            'peak_hour': int(peak_hour),
            'confidence_score': 0.6,  # Lower confidence for simple forecast
            'status': 'success'
        }
    
    def _simple_forecast(self) -> Dict:
        """Simple fallback forecast."""
        current_hour = datetime.now().hour
        hours = [(current_hour + h) % 24 for h in range(24)]
        risks = [0.5 + 0.2 * np.sin(h / 24 * 2 * np.pi) for h in range(24)]
        
        return {
            'hourly_forecast': [
                {'hour': h, 'risk': float(r), 'timestamp': ''}
                for h, r in zip(hours, risks)
            ],
            'peak_hour': int(np.argmax(risks)),
            'confidence_score': 0.3,
            'status': 'success'
        }

# Global instance
_forecasting_service = None

def get_forecasting_service() -> ForecastingService:
    """Get global forecasting service instance."""
    global _forecasting_service
    if _forecasting_service is None:
        _forecasting_service = ForecastingService()
    return _forecasting_service
