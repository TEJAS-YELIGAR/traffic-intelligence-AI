"""
Time-series forecasting service for 24-hour risk prediction.
Uses rolling window and simple regression-based forecasting.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from services.logger import setup_logger

logger = setup_logger(__name__)

class TimeSeriesForecaster:
    """
    Simple time-series forecaster for accident risk prediction.
    Uses last 24 hours rolling risk and regression-based forecast.
    """
    
    def __init__(self, window_size: int = 24):
        """
        Initialize forecaster.
        
        Args:
            window_size: Number of hours to use for rolling window
        """
        self.window_size = window_size
        self.historical_risks = []
    
    def add_observation(self, risk: float, timestamp: datetime = None):
        """
        Add a new risk observation to the historical data.
        
        Args:
            risk: Risk probability (0-1)
            timestamp: Optional timestamp, defaults to now
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.historical_risks.append({
            "timestamp": timestamp,
            "risk": risk
        })
        
        # Keep only last window_size observations
        if len(self.historical_risks) > self.window_size:
            self.historical_risks = self.historical_risks[-self.window_size:]
    
    def forecast_24h(self) -> List[Dict]:
        """
        Generate 24-hour risk forecast using simple methods.
        
        Returns:
            List of dictionaries with 'hour' and 'risk' keys
        """
        if len(self.historical_risks) < 3:
            # Not enough data, return default pattern
            logger.warning("Insufficient historical data, using default forecast")
            return self._default_forecast()
        
        # Extract recent risks
        recent_risks = [obs["risk"] for obs in self.historical_risks[-self.window_size:]]
        
        # Simple forecasting methods:
        # 1. Moving average baseline
        # 2. Trend component (linear regression on recent data)
        # 3. Hourly pattern (if we have enough data)
        
        baseline = np.mean(recent_risks)
        trend = self._calculate_trend(recent_risks)
        hourly_pattern = self._calculate_hourly_pattern()
        
        forecast = []
        current_hour = datetime.now().hour
        
        for h in range(24):
            hour = (current_hour + h) % 24
            
            # Base risk with trend
            base_risk = baseline + (trend * h / 24)
            
            # Apply hourly pattern
            if hourly_pattern:
                hour_factor = hourly_pattern.get(hour, 1.0)
                base_risk = base_risk * hour_factor
            
            # Add some noise for realism
            noise = np.random.normal(0, 0.05)
            risk = np.clip(base_risk + noise, 0.0, 1.0)
            
            forecast.append({
                "hour": hour,
                "risk": float(risk)
            })
        
        logger.debug(f"Generated 24h forecast with baseline={baseline:.3f}, trend={trend:.4f}")
        return forecast
    
    def _calculate_trend(self, risks: List[float]) -> float:
        """Calculate linear trend from recent risks."""
        if len(risks) < 2:
            return 0.0
        
        x = np.arange(len(risks))
        y = np.array(risks)
        
        # Simple linear regression
        coeffs = np.polyfit(x, y, 1)
        return coeffs[0]  # Slope
    
    def _calculate_hourly_pattern(self) -> Dict[int, float]:
        """
        Calculate hourly risk pattern from historical data.
        Returns dictionary mapping hour -> risk multiplier.
        """
        if len(self.historical_risks) < 24:
            return {}
        
        # Group by hour
        hourly_risks = {}
        for obs in self.historical_risks:
            hour = obs["timestamp"].hour
            if hour not in hourly_risks:
                hourly_risks[hour] = []
            hourly_risks[hour].append(obs["risk"])
        
        # Calculate average per hour
        hourly_avg = {h: np.mean(risks) for h, risks in hourly_risks.items()}
        
        # Normalize to multipliers (relative to overall average)
        overall_avg = np.mean(list(hourly_avg.values()))
        if overall_avg > 0:
            hourly_pattern = {h: avg / overall_avg for h, avg in hourly_avg.items()}
        else:
            hourly_pattern = {h: 1.0 for h in hourly_avg.keys()}
        
        return hourly_pattern
    
    def _default_forecast(self) -> List[Dict]:
        """Default forecast when insufficient data."""
        # Typical pattern: higher risk during rush hours (7-9 AM, 5-7 PM)
        rush_hours = [7, 8, 9, 17, 18, 19]
        forecast = []
        
        for h in range(24):
            base_risk = 0.5
            if h in rush_hours:
                base_risk = 0.7
            elif h in [22, 23, 0, 1, 2, 3, 4]:  # Late night/early morning
                base_risk = 0.3
            
            forecast.append({
                "hour": h,
                "risk": base_risk
            })
        
        return forecast

# Global forecaster instance
_forecaster = TimeSeriesForecaster()

def get_forecaster() -> TimeSeriesForecaster:
    """Get global forecaster instance."""
    return _forecaster
