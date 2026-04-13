import time
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..models.schemas import UploadResponse, QueryRequest, QueryResponse, HealthResponse
from ..services.ingestion.csv_loader import CSVLoader
from ..services.query_engine.sql_generator import SQLGenerator
from ..services.query_engine.sql_validator import SQLValidator
from ..services.analytics.chart_selector import ChartSelector
from ..services.analytics.insight_generator import InsightGenerator
from ..ml.anomaly.detector import AnomalyDetector
from ..ml.insights.statistical import StatisticalInsightEngine
from ..utils.session_store import session_store
from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["DataWhisperer"])

csv_loader  = CSVLoader()
sql_gen     = SQLGenerator()
sql_val     = SQLValidator()
chart_sel   = ChartSelector()
insight_gen = InsightGenerator()
anomaly_det = AnomalyDetector()
stat_eng    = StatisticalInsightEngine()


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    fname = file.filename or "upload.csv"
    if not fname.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files supported.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    try:
        df, meta = csv_loader.load(data, fname)
    except ValueError as e:
        raise HTTPException(422, str(e))
    sid = session_store.save(df, meta)
    return UploadResponse(
        success=True,
        session_id=sid,
        filename=fname,
        rows=meta["rows"],
        columns=meta["columns"],
        column_types=meta["column_types"],
        preview=meta["preview"],
        numeric_columns=meta["numeric_columns"],
        categorical_columns=meta["categorical_columns"],
        message="Loaded " + str(meta["rows"]) + " rows and " + str(len(meta["columns"])) + " columns.",
    )


@router.post("/query", response_model=QueryResponse)
async def query_data(body: QueryRequest):
    start = time.time()
    res = session_store.get(body.session_id)
    if not res:
        raise HTTPException(404, "Session not found. Re-upload your CSV.")
    df, meta = res
    try:
        sql, sql_expl = sql_gen.generate(body.question, meta["column_types"])
    except Exception as e:
        raise HTTPException(500, "SQL generation failed: " + str(e))
    try:
        rdf, _ = sql_val.execute(sql, df)
    except ValueError as e:
        ms = round((time.time() - start) * 1000, 1)
        return QueryResponse(
            success=False, question=body.question,
            sql=sql, error=str(e), processing_ms=ms,
        )
    ct, cj   = chart_sel.select_and_build(rdf, body.question)
    ins      = insight_gen.generate(body.question, rdf)
    ms       = round((time.time() - start) * 1000, 1)
    return QueryResponse(
        success=True, question=body.question,
        sql=sql, sql_explanation=sql_expl,
        columns=list(rdf.columns),
        data=rdf.head(500).fillna("").to_dict(orient="records"),
        row_count=len(rdf), chart_type=ct, chart_json=cj,
        insight=ins, processing_ms=ms,
    )


class AnomalyReq(BaseModel):
    session_id: str
    method: Optional[str] = "isolation_forest"


@router.post("/anomaly")
async def detect_anomalies(body: AnomalyReq):
    res = session_store.get(body.session_id)
    if not res:
        raise HTTPException(404, "Session not found. Re-upload your CSV.")
    df, _ = res
    return anomaly_det.detect(df, method=body.method)


class InsightReq(BaseModel):
    session_id: str
    question: Optional[str] = ""


@router.post("/insights")
async def full_insights(body: InsightReq):
    res = session_store.get(body.session_id)
    if not res:
        raise HTTPException(404, "Session not found. Re-upload your CSV.")
    df, _ = res
    return stat_eng.analyze(df, body.question)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        model=settings.llm_model,
        active_sessions=session_store.count(),
    )