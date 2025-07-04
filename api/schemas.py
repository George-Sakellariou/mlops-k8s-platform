from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    version: int
    filename: str
    file_path: str
    metadata: str
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True