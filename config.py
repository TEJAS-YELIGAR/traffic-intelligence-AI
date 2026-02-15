"""
Configuration module for Traffic Accident Risk Prediction application.
Centralizes all configuration settings and environment variables.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Model configuration
MODEL_PATH = MODEL_DIR / "ensemble_model.pkl"
DATA_PATH = DATA_DIR / "US_Accidents.csv"

# Flask configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Model training configuration
TRAIN_TEST_SPLIT = 0.2
RANDOM_STATE = 42
N_ESTIMATORS = 200
MAX_DEPTH = 20
MIN_SAMPLES_SPLIT = 5
MIN_SAMPLES_LEAF = 2

# Feature configuration
CATEGORICAL_FEATURES = ['Weather_Condition']
NUMERICAL_FEATURES = [
    'Visibility(mi)',
    'Temperature(F)',
    'Wind_Speed(mph)',
    'Hour',
    'Is_Weekend',
    'Traffic_Density',
    'Start_Lat',
    'Start_Lng'
]

# Weather condition mapping (for consistent encoding)
WEATHER_CONDITION_MAP = {
    0: "Clear",
    1: "Cloudy",
    2: "Rain",
    3: "Snow",
    4: "Fog",
    5: "Other"
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "logs" / "app.log"

# Create logs directory if it doesn't exist
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Database configuration
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "predictions.db"
DB_DIR.mkdir(exist_ok=True)

# Future API Integration Configuration (Phase 13)
# Structure prepared for external API integrations

# Traffic API Configuration (Future)
TRAFFIC_API_ENABLED = os.getenv("TRAFFIC_API_ENABLED", "False").lower() == "true"
TRAFFIC_API_KEY = os.getenv("TRAFFIC_API_KEY", "")
TRAFFIC_API_URL = os.getenv("TRAFFIC_API_URL", "https://api.traffic.example.com")
TRAFFIC_API_TIMEOUT = int(os.getenv("TRAFFIC_API_TIMEOUT", "5"))

# Weather API Configuration (Future)
WEATHER_API_ENABLED = os.getenv("WEATHER_API_ENABLED", "False").lower() == "true"
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://api.weather.example.com")
WEATHER_API_TIMEOUT = int(os.getenv("WEATHER_API_TIMEOUT", "5"))

# WebSocket Configuration (Future)
WEBSOCKET_ENABLED = os.getenv("WEBSOCKET_ENABLED", "False").lower() == "true"
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "5001"))

# Deployment Configuration (Future)
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "local")  # local, docker, aws, azure
DOCKER_IMAGE_NAME = os.getenv("DOCKER_IMAGE_NAME", "traffic-intelligence")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AZURE_REGION = os.getenv("AZURE_REGION", "eastus")

# Performance Configuration
MAX_PREDICTIONS_CACHE = int(os.getenv("MAX_PREDICTIONS_CACHE", "10000"))
PREDICTION_CACHE_TTL = int(os.getenv("PREDICTION_CACHE_TTL", "3600"))  # seconds

# Geospatial Configuration
DEFAULT_CITY_CENTER = (34.0522, -118.2437)  # Los Angeles
CLUSTER_N_CLUSTERS = int(os.getenv("CLUSTER_N_CLUSTERS", "5"))
HISTORICAL_DATA_HOURS = int(os.getenv("HISTORICAL_DATA_HOURS", "168"))  # 7 days
