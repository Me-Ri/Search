from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ConvertResponse(BaseModel):
    success: bool
    latex_content: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None

class CompareRequest(BaseModel):
    template_content: str = Field(..., min_length=10, description="Текст шаблона")
    document_content: str = Field(..., min_length=10, description="Текст документа")
    model: str = Field(default="gpt-oss:120b-cloud", description="LLM модель")
    parallel: bool = Field(default=True, description="Параллельная проверка")

class ErrorItem(BaseModel):
    section: str
    error_type: Literal["structural", "content", "formatting", "typography"]
    description: str
    severity: Literal["critical", "high", "medium", "low"]

class CompareResponse(BaseModel):
    errors: List[ErrorItem]
    compliance_score: int
    summary: str

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"