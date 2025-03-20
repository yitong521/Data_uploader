from flask import Flask
from celery import Celery
import os

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
           static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

celery = Celery('app',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True
)

from app import views 