import time

from celery import Celery
from celery.schedules import crontab
from flask_mail import Mail, Message

from main import app
from utils import mails_handling

mail = Mail(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

celery.conf.beat_schedule = {
    'mail_every_minute': {
        'task': 'tasks.send_emails',
        'schedule': crontab(
            day_of_month='1-7',
            day_of_week='mon',
            hour=13,
            minute=37
        )
    }
}


@celery.task
def send_emails():
    """
    Sends emails to users with their mean work time.
    """
    data = mails_handling()
    for user in data:
        mean_time = time.strftime(
            '%H:%M:%S',
            time.gmtime(data[user]['mean_time'])
        )

        body = 'Your mean daily work time is {}'.format(mean_time)
        email = [data[user]['email']]

        with app.app_context():
            msg = Message(
                subject='Missing work hours.',
                sender='myapp_stx@o2.pl',
                recipients=email,
                body=body
            )
            mail.send(msg)
    return 'sent'
