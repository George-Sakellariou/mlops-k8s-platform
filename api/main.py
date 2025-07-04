from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import logging
from datetime import datetime
from dotenv import load_dotenv

from config import settings
from database import get_db, engine
from models import Base, Model, ModelVersion
from storage import MinIOStorage
from schemas import ModelCreate, ModelResponse, ModelVersionResponse

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ML Model Registry API",
    description="API for managing ML models and versions",
    version="1.0.0",
    debug=settings.API_DEBUG
)

# Initialize MinIO storage
storage = MinIOStorage()

@app.on_event("startup")
async def startup_event():
    """Initialize storage on startup"""
    logger.info("Starting ML Model Registry API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    logger.info(f"MinIO Endpoint: {settings.MINIO_ENDPOINT}")
    logger.info(f"Model Bucket: {settings.MODEL_BUCKET}")
    
    await storage.create_bucket_if_not_exists()
    logger.info("API startup complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.post("/models/{model_name}/versions", response_model=ModelVersionResponse)
async def upload_model(
    model_name: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
    db: Session = Depends(get_db)
):
    """Upload a new model version"""
    try:
        logger.info(f"Uploading model: {model_name}, file: {file.filename}")
        
        # Get or create model
        model = db.query(Model).filter(Model.name == model_name).first()
        if not model:
            model = Model(name=model_name, description=description or f"Model {model_name}")
            db.add(model)
            db.commit()
            db.refresh(model)
            logger.info(f"Created new model: {model_name}")
        
        # Get next version number
        last_version = db.query(ModelVersion).filter(
            ModelVersion.model_id == model.id
        ).order_by(ModelVersion.version.desc()).first()
        
        next_version = (last_version.version + 1) if last_version else 1
        
        # Upload file to MinIO
        file_content = await file.read()
        file_path = f"{model_name}/v{next_version}/{file.filename}"
        
        await storage.upload_file(file_path, file_content)
        
        # Create model version record
        model_version = ModelVersion(
            model_id=model.id,
            version=next_version,
            file_path=file_path,
            filename=file.filename,
            model_metadata=metadata,
            file_size=len(file_content)
        )
        
        db.add(model_version)
        db.commit()
        db.refresh(model_version)
        
        logger.info(f"Successfully uploaded model {model_name} version {next_version}")
        
        return ModelVersionResponse(
            id=model_version.id,
            model_name=model_name,
            version=model_version.version,
            filename=model_version.filename,
            file_path=model_version.file_path,
            metadata=model_version.model_metadata,
            file_size=model_version.file_size,
            created_at=model_version.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to upload model {model_name}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")

@app.get("/models/{model_name}/versions", response_model=List[ModelVersionResponse])
async def list_model_versions(model_name: str, db: Session = Depends(get_db)):
    """List all versions of a model"""
    logger.info(f"Listing versions for model: {model_name}")
    
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        logger.warning(f"Model not found: {model_name}")
        raise HTTPException(status_code=404, detail="Model not found")
    
    versions = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id
    ).order_by(ModelVersion.version.desc()).all()
    
    logger.info(f"Found {len(versions)} versions for model: {model_name}")
    
    return [
        ModelVersionResponse(
            id=v.id,
            model_name=model_name,
            version=v.version,
            filename=v.filename,
            file_path=v.file_path,
            metadata=v.model_metadata,
            file_size=v.file_size,
            created_at=v.created_at
        ) for v in versions
    ]

@app.get("/models/{model_name}/versions/{version}")
async def download_model(model_name: str, version: int, db: Session = Depends(get_db)):
    """Download a specific model version"""
    logger.info(f"Downloading model: {model_name}, version: {version}")
    
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        logger.warning(f"Model not found: {model_name}")
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_version = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id,
        ModelVersion.version == version
    ).first()
    
    if not model_version:
        logger.warning(f"Model version not found: {model_name} v{version}")
        raise HTTPException(status_code=404, detail="Model version not found")
    
    try:
        file_content = await storage.download_file(model_version.file_path)
        logger.info(f"Successfully downloaded model: {model_name} v{version}")
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={model_version.filename}"}
        )
    except Exception as e:
        logger.error(f"Failed to download model {model_name} v{version}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download model: {str(e)}")

@app.delete("/models/{model_name}/versions/{version}")
async def delete_model_version(model_name: str, version: int, db: Session = Depends(get_db)):
    """Delete a specific model version"""
    logger.info(f"Deleting model: {model_name}, version: {version}")
    
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        logger.warning(f"Model not found: {model_name}")
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_version = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id,
        ModelVersion.version == version
    ).first()
    
    if not model_version:
        logger.warning(f"Model version not found: {model_name} v{version}")
        raise HTTPException(status_code=404, detail="Model version not found")
    
    try:
        # Delete from MinIO
        await storage.delete_file(model_version.file_path)
        
        # Delete from database
        db.delete(model_version)
        db.commit()
        
        logger.info(f"Successfully deleted model: {model_name} v{version}")
        
        return {"message": f"Model {model_name} version {version} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete model {model_name} v{version}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

@app.get("/models", response_model=List[ModelResponse])
async def list_models(db: Session = Depends(get_db)):
    """List all models"""
    logger.info("Listing all models")
    
    models = db.query(Model).all()
    
    logger.info(f"Found {len(models)} models")
    
    return [
        ModelResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            created_at=m.created_at
        ) for m in models
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )