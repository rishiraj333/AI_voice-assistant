import json
import logging
from datetime import datetime

from src.config.settings import settings

logger = logging.getLogger(__name__)

### Backend selection

def _make_store():
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            logger.info("Session store: Redis at %s", settings.redis_url)
            return r
        except Exception as e:
            logger.warning("Redis unavailable (%s), falling back to memory", e)
    logger.info("Session store: in-memory")
    return None

_redis = _make_store()

# fallback in-process store
_memory_store: dict = {}

### Session operations

def get_history(session_id: str) -> list:
    if _redis:
        raw = _redis.get(f"session:{session_id}")
        return json.loads(raw) if raw else []
    return _memory_store.get(session_id, [])

def append_turn(session_id: str, user_text: str, assistant_reply: str) -> None:
    history = get_history(session_id)
    history.append({"role": "user", "content": user_text, "ts": datetime.utcnow().isoformat()})
    history.append({"role": "assistant", "content": assistant_reply, "ts": datetime.utcnow().isoformat()})
    if _redis:
        # 24-hour TTL keeps Redis memory bounded
        _redis.setex(f"session:{session_id}", 86400, json.dumps(history))
    else:
        _memory_store[session_id] = history

def delete_session(session_id: str) -> bool:
    if _redis:
        deleted = _redis.delete(f"session:{session_id}")
        return bool(deleted)
    existed = session_id in _memory_store
    _memory_store.pop(session_id, None)
    return existed
