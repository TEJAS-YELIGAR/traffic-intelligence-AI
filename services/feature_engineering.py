"""
Feature engineering service for traffic accident data.
Extracts temporal features and prepares data for model training.
"""
import pandas as pd
import numpy as np
from services.logger import setup_logger

logger = setup_logger(__name__)

def engineer_features(df):
    """
    Engineer features from raw accident data.
    
    Creates temporal features (Hour, DayOfWeek, Is_Weekend) and
    selects relevant columns for model training.
    
    Args:
        df: DataFrame with raw accident data including 'Start_Time'
        
    Returns:
        DataFrame with engineered features and selected columns
    """
    logger.debug("Engineering features from dataset")
    
    # Convert Start_Time to datetime
    df['Start_Time'] = pd.to_datetime(df['Start_Time'])

    # Extract temporal features
    df['Hour'] = df['Start_Time'].dt.hour
    df['DayOfWeek'] = df['Start_Time'].dt.dayofweek
    df['Is_Weekend'] = (df['DayOfWeek'] >= 5).astype(int)

    # Traffic density (placeholder - in production, this would come from real-time data)
    # TODO: Replace with actual traffic density data source
    df['Traffic_Density'] = np.random.randint(1, 4, size=len(df))

    # Select features for model training
    feature_cols = [
        'Severity',
        'Weather_Condition',
        'Visibility(mi)',
        'Temperature(F)',
        'Wind_Speed(mph)',
        'Hour',
        'Is_Weekend',
        'Traffic_Density',
        'Start_Lat',
        'Start_Lng'
    ]
    
    # Ensure all columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in dataset: {missing_cols}")
        feature_cols = [col for col in feature_cols if col in df.columns]
    
    logger.debug(f"Returning {len(feature_cols)} features")
    return df[feature_cols]
