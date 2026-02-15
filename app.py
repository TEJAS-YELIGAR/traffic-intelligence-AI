"""
Smart City Urban Intelligence Platform - Main Flask Application
Production-ready ML web application with geospatial intelligence,
anomaly detection, and advanced forecasting.
"""
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest
import traceback
import time
from datetime import datetime

from config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT
from services.logger import setup_logger
from services.model_loader import get_model
from services.prediction_service import get_prediction_service
from services.forecasting_service import get_forecasting_service
from services.anomaly_service import get_anomaly_service
from services.geo_service import get_geo_service
from services.chat_service import get_chat_service
from services.validators import ValidationError

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize logger
logger = setup_logger(__name__)

# Initialize services
model_load_start = time.time()
try:
    model = get_model()
    model_load_time = (time.time() - model_load_start) * 1000  # ms
    logger.info(f"Application initialized successfully (model load: {model_load_time:.2f}ms)")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    model = None
    model_load_time = None

# Initialize business services
prediction_service = get_prediction_service()
forecasting_service = get_forecasting_service()
anomaly_service = get_anomaly_service()
geo_service = get_geo_service()
chat_service = get_chat_service()


@app.route("/")
def home():
    """
    Home route - serves the main dashboard.
    
    Returns:
        Rendered dashboard.html template
    """
    logger.info("Dashboard accessed")
    return render_template("dashboard.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
    Prediction endpoint - predicts accident risk with geospatial intelligence.
    
    Request JSON:
        - weather: int (0-5)
        - visibility: float (0-20)
        - temperature: float (-50 to 150)
        - wind_speed: float (0-100)
        - hour: int (0-23)
        - is_weekend: int (0 or 1)
        - traffic_density: float (0-100)
        - latitude: float (-90 to 90)
        - longitude: float (-180 to 180)
    
    Returns:
        JSON with probability, severity, risk_level, geo_features, and anomaly status
    """
    try:
        # Validate request
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        
        data = request.get_json()
        if not data:
            raise BadRequest("Empty request body")
        
        # Use prediction service
        result, processing_time = prediction_service.predict(data)
        
        # Check for anomalies
        is_anomaly = anomaly_service.check_current_anomaly(
            data.get('latitude', 0.0),
            data.get('longitude', 0.0),
            result['probability'],
            result['severity']
        )
        result['is_anomaly'] = is_anomaly
        
        # Add performance metrics
        result['processing_time_ms'] = round(processing_time, 2)
        
        return jsonify(result)
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({
            "error": "Validation failed",
            "message": str(e)
        }), 400
    
    except BadRequest as e:
        logger.warning(f"Bad request: {e}")
        return jsonify({
            "error": "Bad request",
            "message": str(e)
        }), 400
    
    except RuntimeError as e:
        logger.error(f"Prediction service error: {e}", exc_info=True)
        return jsonify({
            "error": "Prediction failed",
            "message": str(e)
        }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in /predict: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }), 500


@app.route("/forecast", methods=["GET"])
def forecast():
    """
    Intelligent time-series forecasting endpoint.
    Uses historical data with seasonality for 24-hour forecast.
    
    Returns:
        JSON with hourly_forecast, peak_hour, and confidence_score
    """
    try:
        forecast_data = forecasting_service.forecast_24h()
        logger.debug("Generated 24h forecast with seasonality")
        return jsonify(forecast_data)
    
    except Exception as e:
        logger.error(f"Forecast failed: {e}", exc_info=True)
        return jsonify({
            "error": "Forecast failed",
            "message": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint with detailed system status.
    
    Returns:
        JSON with application status, model info, and performance metrics
    """
    status = {
        "status": "healthy" if model is not None else "degraded",
        "model_loaded": model is not None,
        "model_load_time_ms": round(model_load_time, 2) if model_load_time else None,
        "services": {
            "prediction": prediction_service.model is not None,
            "forecasting": forecasting_service.forecaster is not None,
            "anomaly": anomaly_service.anomaly_detector is not None,
            "geospatial": geo_service is not None
        },
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(status), 200 if model is not None else 503


@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    """
    Get detected anomalies in recent predictions.
    
    Query params:
        - hours: int (default 24) - hours to analyze
    
    Returns:
        JSON with anomaly information
    """
    try:
        hours = int(request.args.get('hours', 24))
        anomalies = anomaly_service.detect_anomalies(hours=hours)
        return jsonify(anomalies)
    
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        return jsonify({
            "error": "Anomaly detection failed",
            "message": str(e)
        }), 500


@app.route("/api/historical-clusters", methods=["GET"])
def get_historical_clusters():
    """
    Get historical prediction clusters for map visualization.
    
    Query params:
        - hours: int (default 24) - hours to look back
        - limit: int (default 1000) - max records
    
    Returns:
        JSON with historical prediction data
    """
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 1000))
        
        clusters = geo_service.get_historical_clusters(hours=hours, limit=limit)
        return jsonify({
            "clusters": clusters,
            "count": len(clusters),
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Failed to get historical clusters: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to get clusters",
            "message": str(e)
        }), 500


@app.route("/api/risk-clusters", methods=["GET"])
def get_risk_clusters():
    """
    Get high-risk clusters using KMeans clustering.
    
    Query params:
        - n_clusters: int (default 5) - number of clusters
    
    Returns:
        JSON with risk cluster centers
    """
    try:
        n_clusters = int(request.args.get('n_clusters', 5))
        clusters = geo_service.get_risk_clusters(n_clusters=n_clusters)
        return jsonify({
            "clusters": clusters,
            "count": len(clusters),
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Failed to get risk clusters: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to get risk clusters",
            "message": str(e)
        }), 500


@app.route("/api/feature-importance", methods=["GET"])
def get_feature_importance():
    """
    Get SHAP-based feature importance (if available) or model feature importance.
    
    Returns:
        JSON with feature importance scores
    """
    try:
        if model is None:
            return jsonify({
                "error": "Model not loaded",
                "message": "Model is not available"
            }), 503
        
        # Try to get feature importance from model
        try:
            if hasattr(model, 'named_steps'):
                rf_model = model.named_steps.get('model')
                if rf_model and hasattr(rf_model, 'feature_importances_'):
                    importances = rf_model.feature_importances_
                    
                    # Get feature names (simplified - in production, extract from pipeline)
                    feature_names = [
                        'Weather_Condition_*',  # One-hot encoded
                        'Visibility(mi)',
                        'Temperature(F)',
                        'Wind_Speed(mph)',
                        'Hour',
                        'Is_Weekend',
                        'Traffic_Density',
                        'Start_Lat',
                        'Start_Lng'
                    ]
                    
                    # Create feature importance dict
                    importance_dict = {}
                    for i, name in enumerate(feature_names[:len(importances)]):
                        importance_dict[name] = float(importances[i])
                    
                    # Sort by importance
                    sorted_importance = sorted(
                        importance_dict.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    return jsonify({
                        "feature_importance": dict(sorted_importance),
                        "method": "model_internal",
                        "status": "success"
                    })
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        # Fallback
        return jsonify({
            "feature_importance": {
                "Visibility(mi)": 0.25,
                "Temperature(F)": 0.20,
                "Hour": 0.15,
                "Traffic_Density": 0.15,
                "Weather_Condition": 0.10,
                "Wind_Speed(mph)": 0.10,
                "Start_Lat": 0.03,
                "Start_Lng": 0.02
            },
            "method": "estimated",
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}", exc_info=True)
        return jsonify({
            "error": "Feature importance extraction failed",
            "message": str(e)
        }), 500


@app.route("/api/model-confidence", methods=["GET"])
def get_model_confidence():
    """
    Get model confidence indicator.
    
    Returns:
        JSON with confidence score
    """
    try:
        confidence = prediction_service.get_model_confidence()
        return jsonify({
            "confidence_score": confidence,
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Failed to get model confidence: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to get confidence",
            "message": str(e)
        }), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    AI Risk Assistant Chatbot endpoint - Conversational interface.
    
    Request JSON:
        - message: string - User message
        - user_id: string (optional) - User identifier
        
    Returns:
        JSON with reply, action, and structured_data
    """
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        
        data = request.get_json()
        if not data or 'message' not in data:
            raise BadRequest("Missing 'message' field")
        
        message = data.get('message', '').strip()
        if not message:
            raise BadRequest("Message cannot be empty")
        
        user_id = data.get('user_id', 'default')
        
        # Process message
        response = chat_service.process_message(message, user_id)
        
        logger.info(f"Chat response: action={response.get('action')}")
        
        return jsonify(response)
    
    except BadRequest as e:
        logger.warning(f"Bad request in /chat: {e}")
        return jsonify({
            "error": "Bad request",
            "message": str(e),
            "reply": "I didn't understand that. Could you try rephrasing?",
            "action": "none",
            "structured_data": {}
        }), 400
    
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        return jsonify({
            "error": "Chat processing failed",
            "message": str(e),
            "reply": "I encountered an error. Please try again!",
            "action": "none",
            "structured_data": {}
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not found",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


@app.errorhandler(Exception)
def global_exception_handler(error):
    """
    Global exception handler for unhandled exceptions.
    Catches all exceptions not handled by specific handlers.
    """
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == "__main__":
    logger.info(f"Starting Flask application on {FLASK_HOST}:{FLASK_PORT}")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
