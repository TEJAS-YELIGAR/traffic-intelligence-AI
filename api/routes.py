"""
DEPRECATED: This module is kept for backward compatibility but is not actively used.
All API routes are now handled in app.py with proper error handling, validation, and logging.

This file can be removed in future versions if no external dependencies reference it.
"""
from flask import Blueprint, request, jsonify
import joblib
import pandas as pd

api = Blueprint('api', __name__)

# NOTE: This loads model separately - main app uses services/model_loader.py
# This is kept for backward compatibility only
try:
    model = joblib.load("models/ensemble_model.pkl")
except FileNotFoundError:
    model = None

@api.route("/predict", methods=["POST"])
def predict():
    """
    DEPRECATED: Use /predict endpoint in app.py instead.
    This endpoint lacks proper validation, error handling, and logging.
    """
    if model is None:
        return jsonify({
            "error": "Model not loaded",
            "message": "Please use the main /predict endpoint in app.py"
        }), 503

    data = request.json
    df = pd.DataFrame([data])

    prediction = model.predict(df)[0]
    probability = max(model.predict_proba(df)[0])

    return jsonify({
        "severity": int(prediction),
        "probability": float(probability)
    })
