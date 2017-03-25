from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Aruntime.setting')
app=Celery("Aruntime")
app.config_from_object('Aruntime.apps.Aruntime.celeryconfig')


