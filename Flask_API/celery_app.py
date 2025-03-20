from celery import Celery

celery = Celery('app',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True
)

# Import task modules
from app import tasks 