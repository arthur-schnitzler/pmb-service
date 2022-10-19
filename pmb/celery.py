import os
import psutil

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pmb.settings')
celery_max_mem_kilobytes = (psutil.virtual_memory().total * 0.75) / 1024
print('#########')
print(f"{celery_max_mem_kilobytes}")

app = Celery('pmb')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.worker_max_memory_per_child = int(celery_max_mem_kilobytes / 4)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
