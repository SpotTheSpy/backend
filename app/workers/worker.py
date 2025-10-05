from celery import Celery

from app.asgi import config


def create_worker() -> Celery:
    celery = Celery(
        "worker",
        broker=config.rabbitmq_dsn.get_secret_value(),
        backend=config.result_backend_dsn.get_secret_value(),
        include=["app.workers.tasks"]
    )

    celery.conf.update(
        task_time_limit=30,
        worker_max_tasks_per_child=100
    )

    return celery


worker = create_worker()
