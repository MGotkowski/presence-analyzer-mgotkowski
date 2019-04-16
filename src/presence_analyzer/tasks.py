from celery import Celery
from main import app

from celery.schedules import crontab
from utils import send_email_with_data

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


celery.conf.beat_schedule = {
    'mail_every_minute': {
        'task': 'main.send_email',
        'schedule': crontab(),
        # 'args': (email, data)  # generowane dynamicznie

    }
}


@celery.task
def send_email(email, data):
    with app.app_context():
        send_email_with_data(email, data)
    return 'sent'
