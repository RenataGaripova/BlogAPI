# Python modules
import os
from datetime import timedelta

# Django + Third party modules
from celery import Celery
from celery.schedules import crontab

# Project modules
from settings.conf import ENV_ID

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")
CELERY_BROKER_URL = "redis://redis:6379/1"
app = Celery("settings")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "run-every-60-seconds": {
        "task": "blog.tasks.publish_scheduled_posts",
        "schedule": timedelta(seconds=60),
    },
    "run-every-day-3am": {
        "task": "blog.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
    "run-every-day-12am": {
        "task": "blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
}
