from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yatube.settings")

app = Celery('yatube')
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
