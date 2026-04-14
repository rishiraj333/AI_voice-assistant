import base64
import time
import logging
from gtts import gTTS

from src.config.settings import settings
from src.utils.audio_utils import log_elapsed

logger = logging.getLogger(__name__)

LANGUAGE = 'en'

### Audio generation

def generate_audio(text: str, accent_tld: str) -> str:
    start = time.perf_counter()

    audio_obj = gTTS(text=text, lang=LANGUAGE, tld=accent_tld, slow=False)
    audio_obj.save(settings.temp_audio_path)

    log_elapsed("generate_audio", start)
    return settings.temp_audio_path

### Base64 helper (for API responses)

def audio_file_to_base64(file_path: str) -> str:
    # encode so audio can be returned inline in JSON without a separate endpoint
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
