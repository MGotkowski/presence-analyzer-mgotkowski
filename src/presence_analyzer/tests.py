# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday(self):
        """
        Test mean presence time result by weekday for one user
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = [
            ["Mon", 0],
            ["Tue", 30047],
            ["Wed", 24465],
            ["Thu", 23705],
            ["Fri", 0],
            ["Sat", 0],
            ["Sun", 0]
        ]
        self.assertEqual(len(data), 7)
        self.assertListEqual(data, result)

    def test_api_presence_weekday(self):
        """
        Test presence time by weekday for one user
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        result = [
            ["Weekday", "Presence (s)"],
            ["Mon", 0],
            ["Tue", 30047],
            ["Wed", 24465],
            ["Thu", 23705],
            ["Fri", 0],
            ["Sat", 0],
            ["Sun", 0]
        ]
        self.assertListEqual(data, result)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_mean(self):
        """
        Test mean() function.
        """
        mean = utils.mean
        self.assertEqual(0, mean([]))
        self.assertEqual(3, mean([1, 2, 3, 4, 5]))

    def test_interval(self):
        """
        Test interval() function.
        """
        interval = utils.interval
        start = datetime.time(11, 30, 0)
        end = datetime.time(12, 30, 0)
        self.assertEqual(3600, interval(start, end))

    def test_seconds_since_midnight(self):
        """
        Test seconds_since_midnight() function.
        """
        calc_sec = utils.seconds_since_midnight
        time = datetime.time(1, 1, 1)
        self.assertEqual(3661, calc_sec(time))

    def test_group_by_weekday(self):
        """
        Test assigning time to weekdays
        """
        group_by_weekday = utils.group_by_weekday
        data = utils.get_data()
        result = [[], [30047], [24465], [23705], [], [], []]
        self.assertEqual(result, group_by_weekday(data[10]))


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
