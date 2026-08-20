from celery import Celery
import os


worker_cancel_long_running_tasks_on_connection_loss = False
task_acks_late = True          # si pas déjà présent
task_reject_on_worker_lost = False
broker_heartbeat = None        # désactive le heartbeat côté connexion broker
broker_transport_options = {'visibility_timeout': 3600}  # 1h, largement suffisant pour du 15-17s

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'authentification.settings'
)

app = Celery('authentification')

app.config_from_object(
    'django.conf:settings',
    namespace='CELERY'
)

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
