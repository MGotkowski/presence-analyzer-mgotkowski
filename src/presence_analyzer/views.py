# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging

from flask import redirect, abort
from flask_mako import render_template, exceptions

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    group_start_end_by_weekday,
    get_xml_users,
    time_spent_by_day,
    get_mails_receivers,
)


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday')


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns the mean time interval of the user's presence grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_start_end_by_weekday(data[user_id])
    days = [
        (calendar.day_abbr[weekday], (times[0]), times[1])
        for weekday, times in enumerate(weekdays)
        if times[0] > 0 and times[1] > 0
    ]

    return days


@app.route('/<path:path>')
def template_router(path):
    """
    Render template according to given url.
    """
    try:
        return render_template(path + '.html')
    except exceptions.TemplateLookupException:
        return abort(404)


@app.route('/api/v1/users_data', methods=['GET'])
@jsonify
def users_data_view():
    """
    Returns users id, name and avatar.
    """
    data = get_xml_users()

    return [
        {
            'user_id': user,
            'name': data[user]['name'],
            'avatar': '/static/img/user_avatars/{}.png'.format(user),
            'email': data[user]['email']
        }
        for user in data
    ]


@app.route('/api/v1/presence_days/<int:user_id>', methods=['GET'])
@jsonify
def presence_days_view(user_id):
    """
    Creates list of presence days during a year for a user.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    return time_spent_by_day(data[user_id])


@app.route('/api/v1/mails_receivers', methods=['GET'])
@jsonify
def mails_receivers():
    """
    Returns user_id with number of days to next mail.
    """
    return get_mails_receivers()
