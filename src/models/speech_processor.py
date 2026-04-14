import time
import whisper
import logging

from src.config.settings import settings
from src.utils.audio_utils import log_elapsed

logger = logging.getLogger(__name__)

### Model load (once at startup)

# loaded at import time so every request reuses the same model object
_whisper_model = whisper.load_model(settings.whisper_model_size)
logger.info("Whisper model '%s' loaded", settings.whisper_model_size)

### Transcription

def transcribe(audio_path: str) -> str:
    start = time.perf_counter()

    # Load audio and trim to 30 sec
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    # Decode the audio
    result = _whisper_model.transcribe(audio)
    user_text = result["text"]

    log_elapsed("transcribe", start)
    return user_text
