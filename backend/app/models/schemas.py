from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any

class UploadResponse(BaseModel):
    success: bool
    session_id: str
    filename: str
    rows: int
    columns: List[str]
    column_types: Dict[str, str]
    preview: List[Dict[str, Any]]
    numeric_columns: List[str]
    categorical_columns: List[str]
    message: str

class QueryRequest(BaseModel):
    session_id: str
    question: str

    @field_validator("question")
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v

class QueryResponse(BaseModel):
    success: bool
    question: str
    sql: Optional[str] = None
    sql_explanation: Optional[str] = None
    columns: Optional[List[str]] = []
    data: Optional[List[Dict[str, Any]]] = []
    row_count: Optional[int] = None
    chart_type: Optional[str] = None
    chart_json: Optional[str] = None
    insight: Optional[str] = None
    error: Optional[str] = None
    processing_ms: float = 0.0

class HealthResponse(BaseModel):
    status: str
    app_name: str
    active_sessions: int