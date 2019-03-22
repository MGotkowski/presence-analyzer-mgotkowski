# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import logging
import threading
import xml.etree.cElementTree as etree

from json import dumps
from functools import wraps
from datetime import datetime, timedelta

from flask import Response

from presence_analyzer.main import app


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def jsonify(wrapped):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(wrapped)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(wrapped(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def cache(time_to_live):
    """
    Decorator that caches loaded data,
    expire time is set as datetime.now() + time_to_live.
    """
    lock = threading.Lock()

    def cache_decorator(wrapped):
        """
        Create cache for wrapped function.
        """
        cached = {}

        @wraps(wrapped)
        def caching(*args, **kwargs):
            with lock:
                key = (wrapped, args)
                if key in cached and cached[key][1] > datetime.now():
                    return cached[key][0]
                else:
                    result = wrapped(*args, **kwargs)
                    cached[key] = (
                        result,
                        datetime.now() + timedelta(seconds=time_to_live)
                    )
                    return result
        return caching
    return cache_decorator


@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_start_end_by_weekday(items):
    """
    Groups mean start and mean end times by weekday.

    Returns [mean start, mean end] in (s) for each weekday
    """
    # one list for every day in week, two lists for start and end times by day
    weekdays = [
        ([], [])
        for i in range(7)
    ]

    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        weekdays[date.weekday()][0].append(seconds_since_midnight(start))
        weekdays[date.weekday()][1].append(seconds_since_midnight(end))

    result = [
        [int(mean(day[0])), int(mean(day[1]))]
        for day in weekdays
    ]

    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates interval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if items else 0


def get_xml_users():
    """
    Extracts users data from xml file and groups it by id.

    It creates structure like this:
    data = {
        'user_id': {
            'name': 'Anna K.',
            'avatar': intranet.stxnext.pl/api/images/users/176,
        }
        'user_id': {
            'name': 'Jan N.',
            'avatar': intranet.stxnext.pl/api/images/users/16,
        }
    }
    """
    xml_data = etree.parse(app.config['DATA_XML'])
    xml_data = xml_data.getroot()
    users = xml_data[1]
    host = xml_data[0][0].text
    data = {}
    for user in users:
        user_id = int(user.get('id'))
        avatar = user[0].text
        name = user[1].text

        data[user_id] = {'name': name, 'avatar': host + avatar}

    return data
