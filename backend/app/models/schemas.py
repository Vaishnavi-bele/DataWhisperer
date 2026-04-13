from pydantic import BaseModel
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


class QueryResponse(BaseModel):
    success: bool
    question: str
    sql: Optional[str] = None
    sql_explanation: Optional[str] = None
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    chart_type: Optional[str] = None
    chart_json: Optional[str] = None
    insight: Optional[str] = None
    error: Optional[str] = None
    processing_ms: float = 0.0


class HealthResponse(BaseModel):
    status: str
    model: str
    active_sessions: int