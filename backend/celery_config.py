from celery import Celery

celery_app = Celery(
    "file_processor",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.tasks.process_uploaded_file': {'queue': 'file_processing'},
        'app.tasks.process_file_set': {'queue': 'file_set_processing'},
    }
)