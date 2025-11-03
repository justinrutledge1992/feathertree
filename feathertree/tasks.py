# feathertree/tasks.py
from celery import shared_task
import time

@shared_task
def divide(x, y):
    time.sleep(1)
    return x / y