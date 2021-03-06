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
    DATA_XML=MAIN_DATA_XML
)

mako = MakoTemplates(app)
