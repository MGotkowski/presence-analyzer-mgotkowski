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


app = Flask(__name__)  # pylint: disable=invalid-name
app.config.update(
    DEBUG=True,
    DATA_CSV=MAIN_DATA_CSV,
    DATA_XML=MAIN_DATA_XML,

    CELERY_BROKER_URL='amqp://localhost//',

    MAIL_SERVER='',
    MAIL_PORT=465,
    MAIL_USERNAME='',
    MAIL_PASSWORD='',
    MAIL_USE_TLS=False,
    MAIL_USE_SLL=True,
    MAIL_DEFAULT_SENDER='',
)

mako = MakoTemplates(app)
