# https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

# Run this in another process to kickstart redis on Windows:
# celery -A feathertree_project worker -l info -P solo
# celery -A feathertree_project flower --port=5555
# The rest of this tutorial should still apply: 
# https://testdriven.io/courses/django-celery/getting-started/

import os
from celery import Celery
from django.conf import settings

# this code copied from manage.py
# set the default Django settings module for the 'celery' app.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feathertree_project.settings')

# you can change the name here
app = Celery("feathertree_project")

# read config from Django settings, the CELERY namespace would make celery
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# discover and load tasks.py from from all registered Django apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)