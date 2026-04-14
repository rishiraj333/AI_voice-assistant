import time
import numpy as np
import librosa
import logging
from tensorflow.keras.models import load_model

from src.config.settings import settings
from src.utils.audio_utils import log_elapsed

logger = logging.getLogger(__name__)

### Constants

SPEAKER_LABELS = [
    'american', 'welsh', 'telugu', 'bangla',
    'australian', 'british', 'odiya', 'indian', 'malayalam'
]

### Model load (once at startup)

_accent_model = load_model(settings.accent_model_path)
logger.info("Accent model loaded from %s", settings.accent_model_path)

### Feature extraction

def _extract_mfcc(audio_path: str) -> np.ndarray:
    signal, sample_rate = librosa.load(audio_path)
    mfccs = librosa.feature.mfcc(y=signal, sr=sample_rate, n_mfcc=20)
    return mfccs

### Domain mapping

def get_domain(predicted_speaker: str) -> tuple:
    if predicted_speaker == 'american':
        return 'us', 'American'
    elif predicted_speaker == 'australian':
        return 'com.au', 'Australian'
    elif predicted_speaker in ['welsh', 'british']:
        return 'co.uk', 'British'
    else:
        return 'co.in', 'Indian'

### Prediction

def predict_accent(audio_path: str) -> tuple:
    start = time.perf_counter()

    mfccs = _extract_mfcc(audio_path)

    # mean aggregation must match training: np.mean(mfcc.T, axis=0)
    mfcc_mean = np.mean(mfccs.T, axis=0)
    mfcc_mean = np.expand_dims(mfcc_mean, axis=0)

    predicted_index = np.argmax(_accent_model.predict(mfcc_mean), axis=-1)[0]
    predicted_speaker = SPEAKER_LABELS[predicted_index]
    tld, accent_display = get_domain(predicted_speaker)

    log_elapsed("predict_accent", start)
    return predicted_speaker, tld, accent_display
