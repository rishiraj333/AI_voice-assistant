import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s"
)

### FastAPI app

app = FastAPI(
    title="AI Voice Assistant API",
    version="1.0.0",
    description="Accent-aware voice assistant: Whisper → ANN → GPT-3.5 → gTTS"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
