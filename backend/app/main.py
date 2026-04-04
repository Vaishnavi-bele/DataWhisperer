import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .core.config import settings

# -----------------------
# Logging Configuration
# -----------------------
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger(__name__)

# -----------------------
# FastAPI App
# -----------------------
app = FastAPI(
    title=settings.app_name,
    description="Ask questions about CSV data in plain English.",
    version="1.0.0",
)

# -----------------------
# CORS Configuration
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev (restrict in production)
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Routes
# -----------------------
app.include_router(router, prefix=settings.api_prefix)

# -----------------------
# Root Endpoint
# -----------------------
@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running 🔮",
        "docs": f"{settings.api_prefix}/docs" if settings.api_prefix else "/docs",
    }