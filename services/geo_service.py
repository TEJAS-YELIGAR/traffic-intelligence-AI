"""
Geospatial Intelligence Service
Converts raw coordinates into engineered geo-features for better predictions.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple, Optional
import sqlite3
from pathlib import Path
from datetime import datetime
from services.logger import setup_logger

logger = setup_logger(__name__)

class GeospatialService:
    """
    Service for geospatial feature engineering and historical data management.
    """
    
    def __init__(self, db_path: str = "data/predictions.db"):
        """
        Initialize geospatial service.
        
        Args:
            db_path: Path to SQLite database for storing predictions
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        
        # Default city center (Los Angeles - can be configured)
        self.city_center = (34.0522, -118.2437)
        
        # Major highways (simulated - in production, use real GIS data)
        self.highways = [
            (34.0522, -118.2437),  # I-10
            (34.0689, -118.4452),  # I-405
            (34.1478, -118.1445),  # I-5
            (34.0522, -118.2437),  # US-101
        ]
        
        # Region clusters (KMeans model)
        self.region_clusterer = None
        self._load_or_train_clusters()
    
    def _init_database(self):
        """Initialize SQLite database for storing predictions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    probability REAL NOT NULL,
                    severity INTEGER NOT NULL,
                    weather INTEGER,
                    visibility REAL,
                    temperature REAL,
                    wind_speed REAL,
                    hour INTEGER,
                    is_weekend INTEGER,
                    traffic_density REAL,
                    distance_to_highway REAL,
                    distance_to_city_center REAL,
                    urban_density_score REAL,
                    region_cluster INTEGER
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON predictions(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_location 
                ON predictions(latitude, longitude)
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
    
    def _load_or_train_clusters(self):
        """Load or train KMeans clusters for region classification."""
        try:
            # Load historical predictions to train clusters
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT latitude, longitude FROM predictions LIMIT 1000",
                conn
            )
            conn.close()
            
            if len(df) < 10:
                # Not enough data, use default clusters
                logger.warning("Insufficient data for clustering, using defaults")
                self.region_clusterer = None
                return
            
            # Train KMeans with 5 clusters
            self.region_clusterer = KMeans(n_clusters=5, random_state=42, n_init=10)
            self.region_clusterer.fit(df[['latitude', 'longitude']].values)
            logger.info("Region clusters trained successfully")
        
        except Exception as e:
            logger.warning(f"Could not train clusters: {e}")
            self.region_clusterer = None
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two points in kilometers.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = (sin(delta_lat / 2) ** 2 +
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def engineer_geo_features(self, latitude: float, longitude: float) -> Dict[str, float]:
        """
        Engineer geospatial features from coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with geo-features
        """
        # Distance to nearest highway
        distances_to_highways = [
            self.calculate_distance(latitude, longitude, hw_lat, hw_lon)
            for hw_lat, hw_lon in self.highways
        ]
        distance_to_highway = min(distances_to_highways) if distances_to_highways else 10.0
        
        # Distance to city center
        distance_to_city_center = self.calculate_distance(
            latitude, longitude,
            self.city_center[0], self.city_center[1]
        )
        
        # Urban density score (simulated based on distance to center)
        # Closer to center = higher density
        urban_density_score = max(0.0, min(1.0, 1.0 - (distance_to_city_center / 50.0)))
        
        # Region cluster
        region_cluster = 0
        if self.region_clusterer is not None:
            try:
                region_cluster = int(self.region_clusterer.predict(
                    np.array([[latitude, longitude]])
                )[0])
            except Exception as e:
                logger.warning(f"Cluster prediction failed: {e}")
        
        return {
            'distance_to_highway': round(distance_to_highway, 2),
            'distance_to_city_center': round(distance_to_city_center, 2),
            'urban_density_score': round(urban_density_score, 3),
            'region_cluster': region_cluster
        }
    
    def store_prediction(self, latitude: float, longitude: float,
                        probability: float, severity: int,
                        features: Dict, geo_features: Dict):
        """
        Store prediction in database.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            probability: Risk probability
            severity: Predicted severity
            features: Original input features
            geo_features: Engineered geo-features
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO predictions (
                    latitude, longitude, probability, severity,
                    weather, visibility, temperature, wind_speed,
                    hour, is_weekend, traffic_density,
                    distance_to_highway, distance_to_city_center,
                    urban_density_score, region_cluster
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                latitude, longitude, probability, severity,
                features.get('weather', 0),
                features.get('visibility', 10.0),
                features.get('temperature', 70.0),
                features.get('wind_speed', 5.0),
                features.get('hour', 12),
                features.get('is_weekend', 0),
                features.get('traffic_density', 50.0),
                geo_features['distance_to_highway'],
                geo_features['distance_to_city_center'],
                geo_features['urban_density_score'],
                geo_features['region_cluster']
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Prediction stored: ({latitude}, {longitude})")
        
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}", exc_info=True)
    
    def get_historical_clusters(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """
        Get historical prediction clusters for visualization.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records
            
        Returns:
            List of prediction records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT latitude, longitude, probability, severity, timestamp
                FROM predictions
                WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(hours, limit))
            conn.close()
            
            return df.to_dict('records')
        
        except Exception as e:
            logger.error(f"Failed to get historical clusters: {e}", exc_info=True)
            return []
    
    def get_risk_clusters(self, n_clusters: int = 5) -> List[Dict]:
        """
        Get high-risk clusters using KMeans.
        
        Args:
            n_clusters: Number of clusters
            
        Returns:
            List of cluster centers with average risk
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            df = pd.read_sql_query("""
                SELECT latitude, longitude, probability
                FROM predictions
                WHERE timestamp >= datetime('now', '-24 hours')
                LIMIT 5000
            """, conn)
            
            conn.close()
            
            if len(df) < n_clusters:
                return []
            
            # Cluster by location
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(df[['latitude', 'longitude']])
            
            # Calculate average risk per cluster
            clusters = []
            for cluster_id in range(n_clusters):
                cluster_data = df[df['cluster'] == cluster_id]
                if len(cluster_data) > 0:
                    clusters.append({
                        'latitude': float(cluster_data['latitude'].mean()),
                        'longitude': float(cluster_data['longitude'].mean()),
                        'average_risk': float(cluster_data['probability'].mean()),
                        'count': int(len(cluster_data))
                    })
            
            # Sort by risk
            clusters.sort(key=lambda x: x['average_risk'], reverse=True)
            
            return clusters
        
        except Exception as e:
            logger.error(f"Failed to get risk clusters: {e}", exc_info=True)
            return []

# Global instance
_geo_service = None

def get_geo_service() -> GeospatialService:
    """Get global geospatial service instance."""
    global _geo_service
    if _geo_service is None:
        _geo_service = GeospatialService()
    return _geo_service
