from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
import joblib
import numpy as np
import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MODEL_NAME = os.getenv("MODEL_NAME", "iris-classifier")
MODEL_VERSION = int(os.getenv("MODEL_VERSION", "1"))
MODEL_REGISTRY_URL = os.getenv("MODEL_REGISTRY_URL", "http://model-registry-service:8000")
INFERENCE_PORT = int(os.getenv("INFERENCE_PORT", "8001"))

# Global variables
model = None
model_metadata = {}
request_count = 0
prediction_count = 0
error_count = 0
start_time = datetime.utcnow()

class PredictionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    features: List[List[float]]
    return_probabilities: bool = False

class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    predictions: List[int]
    probabilities: Optional[List[List[float]]] = None
    model_name: str
    model_version: int
    prediction_time: str

class HealthResponse(BaseModel):
    status: str
    model_name: str
    model_version: int
    model_loaded: bool
    uptime_seconds: float
    predictions_served: int

class MetricsResponse(BaseModel):
    requests_total: int
    predictions_total: int
    errors_total: int
    uptime_seconds: float
    model_info: Dict[str, Any]

async def download_model():
    """Download model from registry"""
    global model, model_metadata
    
    try:
        logger.info(f"Downloading model {MODEL_NAME} v{MODEL_VERSION} from registry...")
        
        # Download model file
        download_url = f"{MODEL_REGISTRY_URL}/models/{MODEL_NAME}/versions/{MODEL_VERSION}"
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Save model temporarily
        model_path = f"/tmp/{MODEL_NAME}_v{MODEL_VERSION}.pkl"
        with open(model_path, "wb") as f:
            f.write(response.content)
        
        # Load model
        model = joblib.load(model_path)
        logger.info(f"Model loaded successfully: {type(model).__name__}")
        
        # Get model metadata (if available)
        try:
            metadata_url = f"{MODEL_REGISTRY_URL}/models/{MODEL_NAME}/versions"
            metadata_response = requests.get(metadata_url, timeout=10)
            if metadata_response.status_code == 200:
                versions = metadata_response.json()
                for version_info in versions:
                    if version_info["version"] == MODEL_VERSION:
                        model_metadata = {
                            "file_size": version_info.get("file_size", 0),
                            "created_at": version_info.get("created_at", ""),
                            "filename": version_info.get("filename", ""),
                            "metadata": version_info.get("metadata", "{}")
                        }
                        break
        except Exception as e:
            logger.warning(f"Could not fetch model metadata: {e}")
        
        # Clean up temporary file
        os.remove(model_path)
        
        logger.info("Model download and loading completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to download/load model: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ML Inference Server...")
    logger.info(f"Model: {MODEL_NAME} v{MODEL_VERSION}")
    logger.info(f"Registry URL: {MODEL_REGISTRY_URL}")
    
    try:
        await download_model()
        logger.info("Inference server startup complete")
    except Exception as e:
        logger.error(f"Failed to start inference server: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down inference server...")

app = FastAPI(
    title="ML Inference Server",
    description=f"Inference server for {MODEL_NAME} v{MODEL_VERSION}",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make predictions using the loaded model"""
    global request_count, prediction_count, error_count
    
    request_count += 1
    
    if model is None:
        error_count += 1
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert input to numpy array
        X = np.array(request.features)
        
        # Validate input shape
        if X.ndim != 2:
            error_count += 1
            raise HTTPException(
                status_code=400, 
                detail=f"Input must be 2D array, got shape {X.shape}"
            )
        
        # Make predictions
        predictions = model.predict(X).tolist()
        prediction_count += len(predictions)
        
        response_data = {
            "predictions": predictions,
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "prediction_time": datetime.utcnow().isoformat()
        }
        
        # Add probabilities if requested and model supports it
        if request.return_probabilities:
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X).tolist()
                response_data["probabilities"] = probabilities
            else:
                logger.warning("Model does not support probability predictions")
        
        logger.info(f"Served {len(predictions)} predictions")
        
        return PredictionResponse(**response_data)
        
    except Exception as e:
        error_count += 1
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_loaded=model is not None,
        uptime_seconds=uptime,
        predictions_served=prediction_count
    )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get server metrics"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return MetricsResponse(
        requests_total=request_count,
        predictions_total=prediction_count,
        errors_total=error_count,
        uptime_seconds=uptime,
        model_info={
            "name": MODEL_NAME,
            "version": MODEL_VERSION,
            "type": type(model).__name__ if model else "Not loaded",
            "metadata": model_metadata
        }
    )

@app.get("/model-info")
async def get_model_info():
    """Get detailed model information"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    info = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_type": type(model).__name__,
        "model_loaded": True,
        "metadata": model_metadata
    }
    
    # Add model-specific info if available
    if hasattr(model, 'feature_importances_'):
        info["feature_importances"] = model.feature_importances_.tolist()
    
    if hasattr(model, 'classes_'):
        info["classes"] = model.classes_.tolist()
    
    if hasattr(model, 'n_features_in_'):
        info["n_features"] = model.n_features_in_
    
    return info

@app.post("/reload-model")
async def reload_model():
    """Reload model from registry"""
    try:
        logger.info("Reloading model from registry...")
        await download_model()
        return {"message": f"Model {MODEL_NAME} v{MODEL_VERSION} reloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to reload model: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=INFERENCE_PORT)