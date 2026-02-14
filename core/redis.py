# core/redis.py

class DummyRedis:
    def get(self, *args, **kwargs):
        return None

    def setex(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        return None

    def scan_iter(self, *args, **kwargs):
        return []

redis_client = DummyRedis()
