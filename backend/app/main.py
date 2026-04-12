from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="DataWhisperer")
app.include_router(router)