# scripts/models.py
from pydantic import BaseModel, Field
from typing import Literal

class PDFChunk(BaseModel):
    page: int = Field(gt=0)
    type: Literal['text', 'table', 'image']
    content: str
