from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )
    
    id: int
    model_name: str
    version: int
    filename: str
    file_path: str
    metadata: str
    file_size: Optional[int]
    created_at: datetime