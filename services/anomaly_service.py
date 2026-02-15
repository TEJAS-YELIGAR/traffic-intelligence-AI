"""
Anomaly Detection Service
Uses IsolationForest to detect unusual risk spikes.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Optional, Tuple
from services.logger import setup_logger
from services.geo_service import get_geo_service

logger = setup_logger(__name__)

class AnomalyService:
    """
    Service for detecting anomalous risk patterns.
    """
    
    def __init__(self):
        """Initialize anomaly detection service."""
        self.geo_service = get_geo_service()
        self.anomaly_detector = None
        self._train_detector()
    
    def _train_detector(self):
        """Train IsolationForest anomaly detector."""
        try:
            # Load recent predictions
            historical = self.geo_service.get_historical_clusters(hours=168)  # 7 days
            
            if len(historical) < 50:
                logger.warning("Insufficient data for anomaly detector training")
                self.anomaly_detector = None
                return
            
            df = pd.DataFrame(historical)
            
            # Features: probability, severity, location, time features
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Prepare features
            features = df[['probability', 'severity', 'latitude', 'longitude', 
                          'hour', 'day_of_week']].values
            
            # Train IsolationForest
            self.anomaly_detector = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            self.anomaly_detector.fit(features)
            
            logger.info("Anomaly detector trained successfully")
        
        except Exception as e:
            logger.warning(f"Anomaly detector training failed: {e}")
            self.anomaly_detector = None
    
    def detect_anomalies(self, hours: int = 24) -> Dict:
        """
        Detect anomalies in recent predictions.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with anomaly information
        """
        try:
            historical = self.geo_service.get_historical_clusters(hours=hours)
            
            if len(historical) < 10:
                return {
                    'has_anomalies': False,
                    'anomaly_count': 0,
                    'anomalies': [],
                    'message': 'Insufficient data'
                }
            
            df = pd.DataFrame(historical)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            if self.anomaly_detector is None:
                # Simple threshold-based detection
                return self._threshold_detection(df)
            
            # Prepare features
            features = df[['probability', 'severity', 'latitude', 'longitude',
                          'hour', 'day_of_week']].values
            
            # Predict anomalies
            predictions = self.anomaly_detector.predict(features)
            anomaly_scores = self.anomaly_detector.score_samples(features)
            
            # Get anomaly indices (-1 = anomaly, 1 = normal)
            anomaly_indices = np.where(predictions == -1)[0]
            
            if len(anomaly_indices) == 0:
                return {
                    'has_anomalies': False,
                    'anomaly_count': 0,
                    'anomalies': [],
                    'message': 'No anomalies detected'
                }
            
            # Extract anomaly details
            anomalies = []
            for idx in anomaly_indices:
                row = df.iloc[idx]
                anomalies.append({
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'probability': float(row['probability']),
                    'severity': int(row['severity']),
                    'anomaly_score': float(anomaly_scores[idx]),
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp'])
                })
            
            # Sort by anomaly score (more negative = more anomalous)
            anomalies.sort(key=lambda x: x['anomaly_score'])
            
            return {
                'has_anomalies': True,
                'anomaly_count': len(anomalies),
                'anomalies': anomalies[:10],  # Top 10
                'message': f'{len(anomalies)} anomalies detected'
            }
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}", exc_info=True)
            return {
                'has_anomalies': False,
                'anomaly_count': 0,
                'anomalies': [],
                'message': f'Detection error: {str(e)}'
            }
    
    def _threshold_detection(self, df: pd.DataFrame) -> Dict:
        """
        Simple threshold-based anomaly detection fallback.
        
        Args:
            df: DataFrame with predictions
            
        Returns:
            Anomaly detection results
        """
        # High risk threshold
        high_risk_threshold = df['probability'].quantile(0.95)
        
        anomalies = []
        for _, row in df.iterrows():
            if row['probability'] >= high_risk_threshold:
                anomalies.append({
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'probability': float(row['probability']),
                    'severity': int(row['severity']),
                    'anomaly_score': -1.0,  # Placeholder
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp'])
                })
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'anomaly_count': len(anomalies),
            'anomalies': anomalies[:10],
            'message': f'{len(anomalies)} high-risk anomalies detected'
        }
    
    def check_current_anomaly(self, latitude: float, longitude: float,
                             probability: float, severity: int) -> bool:
        """
        Check if current prediction is anomalous.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            probability: Risk probability
            severity: Severity level
            
        Returns:
            True if anomalous
        """
        if self.anomaly_detector is None:
            # Simple threshold check
            return probability >= 0.8
        
        try:
            from datetime import datetime
            current_time = datetime.now()
            
            features = np.array([[
                probability,
                severity,
                latitude,
                longitude,
                current_time.hour,
                current_time.weekday()
            ]])
            
            prediction = self.anomaly_detector.predict(features)[0]
            return prediction == -1
        
        except Exception as e:
            logger.warning(f"Anomaly check failed: {e}")
            return probability >= 0.8

# Global instance
_anomaly_service = None

def get_anomaly_service() -> AnomalyService:
    """Get global anomaly service instance."""
    global _anomaly_service
    if _anomaly_service is None:
        _anomaly_service = AnomalyService()
    return _anomaly_service
