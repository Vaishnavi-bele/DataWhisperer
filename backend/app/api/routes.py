import time
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..models.schemas import *
from ..services.ingestion.csv_loader import CSVLoader
from ..services.query_engine.sql_generator import SQLGenerator
from ..services.query_engine.sql_validator import SQLValidator
from ..services.analytics.chart_selector import ChartSelector
from ..services.analytics.insight_generator import InsightGenerator
from ..ml.anomaly.detector import AnomalyDetector
from ..ml.insights.statistical import StatisticalInsightEngine
from ..utils.session_store import session_store
from ..core.config import settings

router = APIRouter(prefix="/api")

csv_loader  = CSVLoader()
sql_gen     = SQLGenerator()
sql_val     = SQLValidator()
chart_sel   = ChartSelector()
insight_gen = InsightGenerator()
anomaly_det = AnomalyDetector()
stat_eng    = StatisticalInsightEngine()

# ───────── UPLOAD ─────────
@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    data = await file.read()

    df, meta = csv_loader.load(data, file.filename)
    sid = session_store.save(df, meta)

    return UploadResponse(
        success=True,
        session_id=sid,
        filename=file.filename,
        rows=meta["rows"],
        columns=meta["columns"],
        column_types=meta["column_types"],
        preview=meta["preview"],
        numeric_columns=meta["numeric_columns"],
        categorical_columns=meta["categorical_columns"],
        message=f"Loaded {meta['rows']} rows"
    )

# ───────── QUERY ─────────
@router.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    start = time.time()

    res = session_store.get(body.session_id)
    if not res:
        raise HTTPException(404, "Session not found")

    df, meta = res

    sql, expl = sql_gen.generate(body.question, meta["column_types"])

    try:
        result_df, _ = sql_val.execute(sql, df)
    except Exception as e:
        return QueryResponse(
            success=False,
            question=body.question,
            sql=sql,
            error=str(e)
        )

    # chart
    try:
        ct, cj = chart_sel.select_and_build(result_df, body.question)
    except:
        ct, cj = "table", None

    # insight
    try:
        ins = insight_gen.generate(body.question, result_df)
    except:
        ins = "Insight generation failed."

    return QueryResponse(
        success=True,
        question=body.question,
        sql=sql,
        sql_explanation=expl,
        columns=list(result_df.columns),
        data=result_df.to_dict("records"),
        row_count=len(result_df),
        chart_type=ct,
        chart_json=cj,
        insight=ins,
        processing_ms=round((time.time()-start)*1000,1)
    )

# ───────── HEALTH ─────────
@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        active_sessions=session_store.count()
    )