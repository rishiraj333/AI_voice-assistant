import os
import time
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}

### Validation

def validate_audio_format(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[-1].lower()
    return ext in ALLOWED_EXTENSIONS

### Cleanup

def cleanup_temp_file(file_path: str) -> None:
    # silently skip if file was already removed
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    except OSError as e:
        logger.warning("cleanup failed for %s: %s", file_path, e)

### Timing helper

def log_elapsed(label: str, start: float) -> None:
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s completed in %.1f ms", label, elapsed_ms)
