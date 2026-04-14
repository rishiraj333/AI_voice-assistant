import time
import logging
import tempfile
import os

from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Depends
from pydantic import BaseModel

from src.config.settings import settings
from src.models.speech_processor import transcribe
from src.models.accent_detector import predict_accent
from src.services.tts_service import generate_audio, audio_file_to_base64
from src.services.response_generator import generate_response
from src.services.session_manager import get_history, append_turn, delete_session
from src.utils.audio_utils import validate_audio_format, cleanup_temp_file, log_elapsed

logger = logging.getLogger(__name__)
router = APIRouter()

### Auth

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

### Response schemas

class TranscribeResponse(BaseModel):
    transcript: str
    elapsed_ms: float

class AccentResponse(BaseModel):
    predicted_speaker: str
    tld: str
    accent_display: str
    elapsed_ms: float

class VoiceProcessResponse(BaseModel):
    transcript: str
    accent: str
    tld: str
    reply: str
    audio_b64: str
    elapsed_ms: float

class SessionResponse(BaseModel):
    session_id: str
    history: list

class HealthResponse(BaseModel):
    status: str
    whisper_loaded: bool
    accent_model_loaded: bool

### Helpers

def _save_upload_to_temp(upload: UploadFile) -> str:
    # write incoming bytes to a named temp file so librosa/whisper can open it by path
    suffix = os.path.splitext(upload.filename or "audio.wav")[-1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload.file.read())
    tmp.close()
    return tmp.name

### Endpoints

@router.get("/health", response_model=HealthResponse)
def health_check():
    from src.models.speech_processor import _whisper_model
    from src.models.accent_detector import _accent_model
    return HealthResponse(
        status="ok",
        whisper_loaded=_whisper_model is not None,
        accent_model_loaded=_accent_model is not None
    )

@router.post("/voice/transcribe", response_model=TranscribeResponse,
             dependencies=[Depends(verify_api_key)])
async def transcribe_audio(audio: UploadFile = File(...)):
    tmp_path = _save_upload_to_temp(audio)
    start = time.perf_counter()
    try:
        if not validate_audio_format(tmp_path):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        transcript = transcribe(tmp_path)
        elapsed = (time.perf_counter() - start) * 1000
        return TranscribeResponse(transcript=transcript, elapsed_ms=round(elapsed, 1))
    finally:
        cleanup_temp_file(tmp_path)

@router.post("/voice/detect-accent", response_model=AccentResponse,
             dependencies=[Depends(verify_api_key)])
async def detect_accent(audio: UploadFile = File(...)):
    tmp_path = _save_upload_to_temp(audio)
    start = time.perf_counter()
    try:
        if not validate_audio_format(tmp_path):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        predicted_speaker, tld, accent_display = predict_accent(tmp_path)
        elapsed = (time.perf_counter() - start) * 1000
        return AccentResponse(
            predicted_speaker=predicted_speaker,
            tld=tld,
            accent_display=accent_display,
            elapsed_ms=round(elapsed, 1)
        )
    finally:
        cleanup_temp_file(tmp_path)

@router.post("/voice/process", response_model=VoiceProcessResponse,
             dependencies=[Depends(verify_api_key)])
async def process_voice(
    audio: UploadFile = File(...),
    session_id: str = "default"
):
    tmp_path = _save_upload_to_temp(audio)
    start = time.perf_counter()
    try:
        if not validate_audio_format(tmp_path):
            raise HTTPException(status_code=400, detail="Unsupported audio format")

        transcript = transcribe(tmp_path)
        predicted_speaker, tld, accent_display = predict_accent(tmp_path)

        # build history list for GPT context
        history = get_history(session_id)
        history_texts = [turn["content"] for turn in history]
        history_texts.append(transcript)

        reply = generate_response(history_texts)
        append_turn(session_id, transcript, reply)

        # generate audio and encode for inline JSON response
        audio_path = generate_audio(reply, tld)
        audio_b64 = audio_file_to_base64(audio_path)

        elapsed = (time.perf_counter() - start) * 1000
        return VoiceProcessResponse(
            transcript=transcript,
            accent=accent_display,
            tld=tld,
            reply=reply,
            audio_b64=audio_b64,
            elapsed_ms=round(elapsed, 1)
        )
    finally:
        # clean both the upload temp and the generated MP3
        cleanup_temp_file(tmp_path)
        cleanup_temp_file(settings.temp_audio_path)

@router.get("/sessions/{session_id}", response_model=SessionResponse,
            dependencies=[Depends(verify_api_key)])
def get_session(session_id: str):
    return SessionResponse(session_id=session_id, history=get_history(session_id))

@router.delete("/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
def clear_session(session_id: str):
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
