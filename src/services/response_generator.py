import time
import logging
import openai

from src.config.settings import settings
from src.utils.audio_utils import log_elapsed

logger = logging.getLogger(__name__)

_client = openai.OpenAI(api_key=settings.openai_api_key)

### GPT response

def generate_response(chat_history: list) -> str:
    start = time.perf_counter()

    # System defined role
    messages = [
        {"role": "system", "content": "You are a friendly and helpful AI voice assistant. Generate text responses when provided with a chat history, your text will be used as the answer using text-to-speech API"}
    ]
    messages.append({"role": "user", "content": str(chat_history)})

    chat = _client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = chat.choices[0].message.content
    log_elapsed("generate_response", start)
    return reply
