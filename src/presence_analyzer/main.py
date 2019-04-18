# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
import os.path
from flask import Flask
from flask_mako import MakoTemplates

MAIN_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'sample_data.csv'
)
MAIN_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'users.xml'
)
DB = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'database.db'
)

app = Flask(__name__)  # pylint: disable=invalid-name
app.config.update(
    DEBUG=True,
    DATA_CSV=MAIN_DATA_CSV,
    DATA_XML=MAIN_DATA_XML,

    CELERY_BROKER_URL='amqp://localhost//',
    DATABASE=DB,
    MAIL_SERVER='poczta.o2.pl',
    MAIL_PORT=587,
    MAIL_USERNAME='myapp_stx@o2.pl',
    MAIL_PASSWORD='lubieparufki',
    MAIL_USE_TLS=False,
    MAIL_USE_SLL=True,
)

mako = MakoTemplates(app)


# sudo service rabbitmq-server restart
# sudo rabbitmqctl status
# celery -A tasks.celery worker --loglevel=info
# celery -A tasks.celery beat
