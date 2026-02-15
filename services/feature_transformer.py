"""
Feature transformation service for converting API input to model-ready format.
Handles Weather_Condition encoding and ensures dtype consistency.
"""
import pandas as pd
import numpy as np
from config import WEATHER_CONDITION_MAP
from services.logger import setup_logger

logger = setup_logger(__name__)

def transform_predict_input(data: dict) -> pd.DataFrame:
    """
    Transform API request data to DataFrame matching training format.
    Ensures Weather_Condition is properly encoded as string.
    
    Args:
        data: Dictionary with prediction input features
        
    Returns:
        DataFrame with properly formatted features
    """
    # Map weather code to string (for consistent encoding with training)
    weather_code = data.get("weather", 0)
    weather_condition = WEATHER_CONDITION_MAP.get(weather_code, "Clear")
    
    # Create DataFrame with exact column names and types expected by model
    input_df = pd.DataFrame([{
        "Weather_Condition": weather_condition,  # String, not int!
        "Visibility(mi)": float(data.get("visibility", 10.0)),
        "Temperature(F)": float(data.get("temperature", 70.0)),
        "Wind_Speed(mph)": float(data.get("wind_speed", 5.0)),
        "Hour": int(data.get("hour", 12)),
        "Is_Weekend": int(data.get("is_weekend", 0)),
        "Traffic_Density": float(data.get("traffic_density", 50.0)),
        "Start_Lat": float(data.get("latitude", 0.0)),
        "Start_Lng": float(data.get("longitude", 0.0))
    }])
    
    # Ensure correct dtypes
    input_df["Weather_Condition"] = input_df["Weather_Condition"].astype(str)
    input_df["Hour"] = input_df["Hour"].astype(int)
    input_df["Is_Weekend"] = input_df["Is_Weekend"].astype(int)
    
    logger.debug(f"Transformed input shape: {input_df.shape}, dtypes:\n{input_df.dtypes}")
    
    return input_df
