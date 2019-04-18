import time

from celery import Celery
from main import app

from celery.schedules import crontab
from utils import mails_handling

from flask_mail import Mail, Message

mail = Mail(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

celery.conf.beat_schedule = {
    'mail_every_minute': {
        'task': 'tasks.send_emails',
        'schedule': crontab(),
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

        body = 'Your mean daily work time is {}'.format((user, mean_time))

        with app.app_context():
            msg = Message(
                subject='Missing work hours.',
                recipients=['wutafaga@dreamcatcher.email'],
                sender='myapp_stx@o2.pl',
                body=body
            )
            mail.send(msg)
    return 'sent'
