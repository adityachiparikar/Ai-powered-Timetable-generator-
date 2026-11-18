import redis
from app.core.config import settings

class SolverLogger:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.redis_client = redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0")
        self.log_key = f"solver_logs:{task_id}"

    def log(self, message: str):
        try:
            self.redis_client.rpush(self.log_key, message)
            # Keep logs for 1 hour
            self.redis_client.expire(self.log_key, 3600)
        except redis.RedisError:
            pass

    def get_logs(self):
        try:
            logs = self.redis_client.lrange(self.log_key, 0, -1)
            return [l.decode('utf-8') for l in logs]
        except redis.RedisError:
            return []

    def clear_logs(self):
        try:
            self.redis_client.delete(self.log_key)
        except redis.RedisError:
            pass
