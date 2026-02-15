"""
Model training service with proper feature scaling, separate pipelines,
and comprehensive evaluation metrics.
"""
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from config import (
    MODEL_PATH,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TRAIN_TEST_SPLIT,
    RANDOM_STATE,
    N_ESTIMATORS,
    MAX_DEPTH,
    MIN_SAMPLES_SPLIT,
    MIN_SAMPLES_LEAF
)
from services.logger import setup_logger

logger = setup_logger(__name__)

def train_model(df):
    """
    Train RandomForest model with proper feature scaling and evaluation.
    
    Args:
        df: DataFrame with features and target 'Severity'
        
    Returns:
        Trained pipeline model
    """
    logger.info("Starting model training...")
    
    # Prepare features and target
    X = df.drop("Severity", axis=1)
    y = df["Severity"]
    
    logger.info(f"Training on {len(X)} samples with {len(X.columns)} features")
    logger.info(f"Categorical features: {CATEGORICAL_FEATURES}")
    logger.info(f"Numerical features: {NUMERICAL_FEATURES}")
    
    # Separate preprocessing for categorical and numerical features
    # Categorical: OneHotEncoder
    # Numerical: StandardScaler for proper feature scaling
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
            ('num', StandardScaler(), NUMERICAL_FEATURES)
        ],
        remainder='drop'  # Drop any columns not explicitly specified
    )
    
    # Improved RandomForest with better hyperparameters
    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_split=MIN_SAMPLES_SPLIT,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight='balanced'  # Handle class imbalance
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('prep', preprocessor),
        ('model', model)
    ])
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TRAIN_TEST_SPLIT, random_state=RANDOM_STATE, stratify=y
    )
    
    logger.info(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")
    
    # Train model
    logger.info("Fitting pipeline...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate model
    logger.info("Evaluating model...")
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    
    # ROC-AUC (handle multi-class if needed)
    try:
        if len(np.unique(y)) == 2:
            roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        else:
            roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
    except Exception as e:
        logger.warning(f"Could not calculate ROC-AUC: {e}")
        roc_auc = None
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Log metrics
    logger.info(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    if roc_auc is not None:
        logger.info(f"ROC-AUC: {roc_auc:.4f}")
    logger.info(f"Confusion Matrix:\n{cm}")
    logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")
    
    # Save model
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    logger.info(f"Model saved successfully to {MODEL_PATH}")
    
    return pipeline
