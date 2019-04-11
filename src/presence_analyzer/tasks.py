from main import celery


@celery.task
def my_background_task(string):
    return string[::-1]
