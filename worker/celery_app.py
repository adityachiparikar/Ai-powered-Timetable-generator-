import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['worker.tasks.solver_task']
)

# Default queue will be used

