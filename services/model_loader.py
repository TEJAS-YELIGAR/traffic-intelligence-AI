"""
Model loading service with singleton pattern.
Ensures model is loaded once globally and reused.
"""
import joblib
from pathlib import Path
from config import MODEL_PATH
from services.logger import setup_logger

logger = setup_logger(__name__)

class ModelLoader:
    """
    Singleton class for loading and managing the ML model.
    Ensures model is loaded only once and cached.
    """
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the trained model from disk."""
        try:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
            
            logger.info(f"Loading model from {MODEL_PATH}")
            self._model = joblib.load(MODEL_PATH)
            logger.info("Model loaded successfully")
            
            # Log model type and attributes
            if hasattr(self._model, 'named_steps'):
                logger.debug(f"Model pipeline steps: {list(self._model.named_steps.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}", exc_info=True)
            raise
    
    @property
    def model(self):
        """Get the loaded model instance."""
        if self._model is None:
            self._load_model()
        return self._model
    
    def reload(self):
        """Force reload the model from disk."""
        logger.info("Reloading model...")
        self._model = None
        self._load_model()

# Global model loader instance
_model_loader = None

def get_model():
    """
    Get the global model instance.
    Loads model on first call, then reuses cached instance.
    
    Returns:
        Loaded sklearn pipeline model
    """
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader.model
