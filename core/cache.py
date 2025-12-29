import json
from typing import Any, Optional
from core.redis import redis_client

DEFAULT_TTL = 60  # seconds

def cache_get(key: str) -> Optional[Any]:
    val = redis_client.get(key)
    if not val:
        return None
    return json.loads(val)

def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    redis_client.setex(key, ttl, json.dumps(value, default=str))

def cache_delete(pattern: str):
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
