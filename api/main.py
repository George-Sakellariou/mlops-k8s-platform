from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import os
from datetime import datetime

from database import get_db, engine
from models import Base, Model, ModelVersion
from storage import MinIOStorage
from schemas import ModelCreate, ModelResponse, ModelVersionResponse

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ML Model Registry API",
    description="API for managing ML models and versions",
    version="1.0.0"
)

# Initialize MinIO storage
storage = MinIOStorage()

@app.on_event("startup")
async def startup_event():
    """Initialize storage on startup"""
    await storage.create_bucket_if_not_exists()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

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
        # Get or create model
        model = db.query(Model).filter(Model.name == model_name).first()
        if not model:
            model = Model(name=model_name, description=description or f"Model {model_name}")
            db.add(model)
            db.commit()
            db.refresh(model)
        
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
            model_metadata=metadata,  # Make sure this is 'model_metadata'
            file_size=len(file_content)
        )
        
        db.add(model_version)
        db.commit()
        db.refresh(model_version)
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")

@app.get("/models/{model_name}/versions", response_model=List[ModelVersionResponse])
async def list_model_versions(model_name: str, db: Session = Depends(get_db)):
    """List all versions of a model"""
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    versions = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id
    ).order_by(ModelVersion.version.desc()).all()
    
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
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_version = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id,
        ModelVersion.version == version
    ).first()
    
    if not model_version:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    try:
        file_content = await storage.download_file(model_version.file_path)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={model_version.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download model: {str(e)}")

@app.delete("/models/{model_name}/versions/{version}")
async def delete_model_version(model_name: str, version: int, db: Session = Depends(get_db)):
    """Delete a specific model version"""
    model = db.query(Model).filter(Model.name == model_name).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_version = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id,
        ModelVersion.version == version
    ).first()
    
    if not model_version:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    try:
        # Delete from MinIO
        await storage.delete_file(model_version.file_path)
        
        # Delete from database
        db.delete(model_version)
        db.commit()
        
        return {"message": f"Model {model_name} version {version} deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

@app.get("/models", response_model=List[ModelResponse])
async def list_models(db: Session = Depends(get_db)):
    """List all models"""
    models = db.query(Model).all()
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
    uvicorn.run(app, host="0.0.0.0", port=8000)