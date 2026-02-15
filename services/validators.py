"""
Input validation and schema validation for API endpoints.
Ensures data integrity before model prediction.
"""
from typing import Dict, Any, List, Optional
from services.logger import setup_logger

logger = setup_logger(__name__)

# Expected feature ranges and types
FEATURE_SCHEMA = {
    "weather": {"type": int, "min": 0, "max": 5, "required": True},
    "visibility": {"type": float, "min": 0.0, "max": 20.0, "required": True},
    "temperature": {"type": float, "min": -50.0, "max": 150.0, "required": True},
    "wind_speed": {"type": float, "min": 0.0, "max": 100.0, "required": True},
    "hour": {"type": int, "min": 0, "max": 23, "required": True},
    "is_weekend": {"type": int, "min": 0, "max": 1, "required": True},
    "traffic_density": {"type": float, "min": 0.0, "max": 100.0, "required": True},
    "latitude": {"type": float, "min": -90.0, "max": 90.0, "required": True},
    "longitude": {"type": float, "min": -180.0, "max": 180.0, "required": True}
}

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_predict_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate incoming prediction request data.
    
    Args:
        data: Request JSON data
        
    Returns:
        Validated and normalized data dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    errors = []
    validated_data = {}
    
    # Check required fields and validate types/ranges
    for field, schema in FEATURE_SCHEMA.items():
        if schema["required"] and field not in data:
            errors.append(f"Missing required field: {field}")
            continue
        
        if field in data:
            value = data[field]
            expected_type = schema["type"]
            
            # Type validation
            try:
                if expected_type == int:
                    value = int(value)
                elif expected_type == float:
                    value = float(value)
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                continue
            
            # Range validation
            if "min" in schema and value < schema["min"]:
                errors.append(f"Field '{field}' must be >= {schema['min']}")
                continue
            if "max" in schema and value > schema["max"]:
                errors.append(f"Field '{field}' must be <= {schema['max']}")
                continue
            
            validated_data[field] = value
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warning(f"Validation failed: {error_msg}")
        raise ValidationError(error_msg)
    
    logger.debug(f"Validation successful for request: {list(validated_data.keys())}")
    return validated_data
