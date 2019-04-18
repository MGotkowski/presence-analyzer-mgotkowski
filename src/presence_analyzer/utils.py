# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
import sqlite3
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
            'email': 'anna_k@myapp.com'
        }
        'user_id': {
            'name': 'Jan N.',
            'avatar': intranet.stxnext.pl/api/images/users/16,
            'email': 'jan_n@myapp.com'
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
        email = user[2].text

        data[user_id] = {
            'name': name,
            'avatar': host + avatar,
            'email': email,
        }
    return data


def time_spent_by_day(items):
    """
    Calculate time of presence grouped by day.
    """
    result = []
    for date in items:
        day = str(date)
        start = items[date]['start']
        end = items[date]['end']
        result.append([
            day,
            interval(start, end) / 60,
        ])
    return result


def mean_work_time():
    """
    Returns 5 users that work for at least 4 months
    with the lowest mean work time in 2013.
    """
    data = get_data()

    users_data = {}
    for user in data:

        months = [0 for _ in range(9)]  # each 0 for months 01-09.2013
        for date in data[user]:

            if date.year == 2013:
                start = data[user][date]['start']
                end = data[user][date]['end']
                months[date.month - 1] += interval(start, end)

        users_data[user] = months

    result = (
        (
            user,
            sum(users_data[user]) / 189  # time(s) / workdays for 01-09.2013
        )
        for user in users_data
        # people that work for at least 4 months
        if users_data[user].count(0) < 4
    )

    return sorted(result, key=lambda v: v[1])[:5]


def mails_handling():  # async task
    """
    Deletes old data, returns users for sending emails
    and adds them to the database.
    """
    users_data = get_xml_users()
    data = mean_work_time()

    result = {}

    cnx = sqlite3.connect(app.config['DATABASE'])
    cursor = cnx.cursor()

    # delete old data
    cursor.execute(
        'DELETE FROM mean_time WHERE next_mail < ?',
        (datetime.now().date().strftime('%Y-%m-%d'),)
    )

    # get users that already have received an email
    cursor.execute('SELECT user_id FROM mean_time')
    blocked_users = [user_id for (user_id,) in cursor]

    # add users users that will receive an email to database
    for (user, mean_time) in data:
        if user in users_data and user not in blocked_users:
            result[user] = {
                'mean_time': mean_time,
                'email': users_data[user]['email'],
            }

            next_mail = (
                datetime.now().date() + timedelta(days=120)
            ).strftime('%Y-%m-%d')

            insert = '''
            INSERT INTO mean_time(user_id, mean_time, next_mail) 
            SELECT ?, ?, ?
            WHERE NOT EXISTS(SELECT user_id FROM mean_time WHERE user_id=?)
            '''

            cursor.execute(insert, (user, mean_time, next_mail, user))

    cnx.commit()
    cursor.close()
    cnx.close()
    return result


def get_mails_receivers():
    """
    Returns users and days left for sending next emails.
    """
    cnx = sqlite3.connect(app.config['DATABASE'])
    cursor = cnx.cursor()
    cursor.execute('SELECT user_id, next_mail FROM mean_time;')

    result = {}
    for user_id, next_mail in cursor:
        next_mail = datetime.strptime(next_mail, '%Y-%m-%d').date()
        days_to_next_mail = next_mail - datetime.now().date()
        result[user_id] = days_to_next_mail.days

    cursor.close()
    cnx.close()

    return result
