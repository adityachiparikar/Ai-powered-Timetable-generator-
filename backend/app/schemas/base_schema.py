from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class IDSchema(SchemaBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
