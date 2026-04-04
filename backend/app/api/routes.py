import time
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException

from ..models.schemas import UploadResponse, QueryRequest, QueryResponse, HealthResponse
from ..services.ingestion.csv_loader import CSVLoader
from ..services.query_engine.sql_generator import SQLGenerator
from ..services.query_engine.sql_validator import SQLValidator
from ..services.analytics.chart_selector import ChartSelector
from ..services.analytics.insight_generator import InsightGenerator
from ..utils.session_store import session_store
from ..core.config import settings

logger = logging.getLogger(__name__)

# Router (no prefix here — handled in main.py)
router = APIRouter(tags=["DataWhisperer"])

# Constants
MAX_FILE_SIZE_MB = 5
MAX_ROWS = 500

# Services (single instance)
csv_loader        = CSVLoader()
sql_generator     = SQLGenerator()
sql_validator     = SQLValidator()
chart_selector    = ChartSelector()
insight_generator = InsightGenerator()


# -----------------------
# Upload CSV
# -----------------------
@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    filename = file.filename or "upload.csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(400, f"Only CSV files supported. Got: '{filename}'")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(400, "File is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, "File too large (max 5MB).")

    try:
        df, metadata = csv_loader.load(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(422, str(e))

    session_id = session_store.save(df, metadata)

    logger.info(f"Uploaded file '{filename}' → session {session_id}")

    return UploadResponse(
        success=True,
        session_id=session_id,
        filename=filename,
        rows=metadata["rows"],
        columns=metadata["columns"],
        column_types=metadata["column_types"],
        preview=metadata["preview"],
        message=f"Loaded {metadata['rows']:,} rows and {len(metadata['columns'])} columns.",
    )


# -----------------------
# Query Data
# -----------------------
@router.post("/query", response_model=QueryResponse)
async def query_data(body: QueryRequest):
    start = time.time()

    logger.info(f"Query received: {body.question}")

    result = session_store.get(body.session_id)
    if not result:
        raise HTTPException(404, f"Session '{body.session_id}' not found. Re-upload your CSV.")

    df, metadata = result

    # Step 1: Generate SQL
    try:
        sql, sql_explanation = sql_generator.generate(
            question=body.question,
            schema=metadata["column_types"],
        )
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise HTTPException(500, "SQL generation failed.")

    # Step 2: Execute SQL
    try:
        result_df, status = sql_validator.execute(sql, df)
    except ValueError as e:
        return QueryResponse(
            success=False,
            question=body.question,
            sql=sql,
            error=str(e),
            processing_ms=round((time.time() - start) * 1000, 1),
        )

    # Step 3: Chart
    try:
        chart_type, chart_json = chart_selector.select_and_build(result_df, body.question)
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        chart_type, chart_json = "table", None

    # Step 4: Insight
    try:
        insight = insight_generator.generate(body.question, result_df)
    except Exception as e:
        logger.warning(f"Insight generation failed: {e}")
        insight = "Insight generation failed."

    return QueryResponse(
        success=True,
        question=body.question,
        sql=sql,
        sql_explanation=sql_explanation,
        columns=list(result_df.columns),
        data=result_df.head(MAX_ROWS).to_dict(orient="records"),
        row_count=len(result_df),
        chart_type=chart_type,
        chart_json=chart_json,
        insight=insight,
        processing_ms=round((time.time() - start) * 1000, 1),
    )


# -----------------------
# Health Check
# -----------------------
@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        model=settings.llm_model,
        active_sessions=session_store.count(),
    )