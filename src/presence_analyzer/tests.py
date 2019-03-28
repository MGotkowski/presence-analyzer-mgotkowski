# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from mock import patch, MagicMock

from presence_analyzer import main, utils, views


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'runtime',
    'data',
    'test_data.csv'
)

MALF_DATA_CSV = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'runtime',
    'data',
    'malformed_data.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'runtime',
    'data',
    'test_users.xml'
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
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_template_router(self):
        """
        Test template_router redirect.
        """
        resp = self.client.get('/presence_weekday')
        self.assertEqual(resp.status_code, 200)
        source = resp.get_data()
        self.assertIn('<h2>Presence by weekday</h2>', source)

    def test_template_router_wrong_url(self):
        """
        Test template_router for incorrect url.
        """
        resp = self.client.get('/wrong_url')
        self.assertEqual(resp.status_code, 404)

    def test_api_users_data(self):
        """
        Test users data listing.
        """
        resp = self.client.get('/api/v1/users_data')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 5)
        self.assertDictEqual(
            data[0],
            {
                'user_id': 1,
                'name': 'Adam A.',
                'avatar': '/static/img/user_avatars/1.png',
            }
        )

    def test_api_mean_time_weekday(self):
        """
        Test mean presence time result by weekday for one user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = [
            ['Mon', 0],
            ['Tue', 30047],
            ['Wed', 24465],
            ['Thu', 23705],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ]
        self.assertListEqual(data, result)

    @patch('presence_analyzer.views.log')
    def test_api_mean_time_weekday_wrong_data(self, mock_log):
        """
        Test mean presence time for user that is not in data.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/1')
        self.assertTrue(mock_log.debug.called)
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_weekday(self):
        """
        Test presence time by weekday for one user.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = [
            ['Weekday', 'Presence (s)'],
            ['Mon', 0],
            ['Tue', 30047],
            ['Wed', 24465],
            ['Thu', 23705],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ]
        self.assertListEqual(data, result)

    @patch('presence_analyzer.views.log')
    def test_api_presence_weekday_wrong_data(self, mock_log):
        """
        Test presence time by weekday for user that is not in data.
        """
        resp = self.client.get('/api/v1/presence_weekday/1')
        self.assertTrue(mock_log.debug.called)
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_start_end(self):
        """
        Test presence start and end time by weekday for one user.
        """
        resp = self.client.get('/api/v1/presence_start_end/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = [
            ['Mon', 33134, 57257],
            ['Tue', 33590, 50154],
            ['Wed', 33206, 58527],
            ['Thu', 35602, 58586],
            ['Fri', 47816, 54242],
        ]
        self.assertEqual(data, result)

    @patch('presence_analyzer.views.log')
    def test_api_presence_start_end_wrong_data(self, mock_log):
        """
        Test presence start and end time by weekday
        for user that is not in data.
        """
        resp = self.client.get('/api/v1/presence_start_end/1')
        mock_log.debug.assert_called_with('User %s not found!', 1)
        self.assertEqual(resp.status_code, 404)

    def test_api_days_of_presence(self):
        """
        Test days of presence for one user.
        """
        resp = self.client.get('/api/v1/presence_days/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = [
            ['2013-09-10', 500],
            ['2013-09-11', 407],
            ['2013-09-12', 395],
        ]

        for _ in result:
            self.assertIn(_, data)

    @patch('presence_analyzer.views.log')
    def test_api_days_of_presence_wrong_data(self, mock_log):
        """
        Test days of presence for a user that is not in data.
        """
        resp = self.client.get('/api/v1/presence_days/1')
        mock_log.debug.assert_called_with('User %s not found!', 1)
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        reload(utils)  # cache-cleaning
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})

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

    @patch.dict(
        'presence_analyzer.main.app.config',
        {'DATA_CSV': MALF_DATA_CSV}
    )
    @patch('presence_analyzer.utils.log')
    def test_malformed_get_data(self, mock_log):
        """
        Test get_data() with malformed data.
        """
        utils.get_data()
        self.assertTrue(mock_log.debug.called)

    def test_get_xml_users(self):
        """
        Test parsing of xml file.
        """
        data = utils.get_xml_users()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), range(1, 6))
        self.assertEqual(len(data), 5)

        self.assertEqual(
            data[1],
            {
                'name': 'Adam A.',
                'avatar': 'http://127.0.0.1:5000/api/images/users/1',
            }
        )

    def test_mean(self):
        """
        Test mean() function.
        """
        self.assertEqual(0, utils.mean([]))
        self.assertEqual(3, utils.mean([1, 2, 3, 4, 5]))

    def test_interval(self):
        """
        Test interval() function.
        """
        self.assertEqual(
            3600,
            utils.interval(
                datetime.time(11, 30, 0),
                datetime.time(12, 30, 0)
            )
        )
        self.assertEqual(
            0,
            utils.interval(
                datetime.time(7, 7, 7),
                datetime.time(7, 7, 7)
            )
        )
        self.assertEqual(
            86399,
            utils.interval(
                datetime.time(0, 0, 0),
                datetime.time(23, 59, 59)
            )
        )
        self.assertEqual(
            3539,
            utils.interval(
                datetime.time(12, 59, 59),
                datetime.time(13, 58, 58)
            )
        )

    def test_seconds_since_midnight(self):
        """
        Test seconds_since_midnight() function.
        """
        self.assertEqual(
            3661,
            utils.seconds_since_midnight(datetime.time(1, 1, 1))
        )
        self.assertEqual(
            0,
            utils.seconds_since_midnight(datetime.time(0, 0, 0))
        )
        self.assertEqual(
            86399,
            utils.seconds_since_midnight(datetime.time(23, 59, 59))
        )

    def test_group_by_weekday(self):
        """
        Test assigning time to weekdays.
        """
        fake_data = {
            datetime.date(2019, 3, 4): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2019, 3, 5): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
        result = [[30600], [29700], [], [], [], [], []]

        self.assertEqual(result, utils.group_by_weekday(fake_data))

    def test_group_start_end_by_weekday(self):
        """
        Test assigning mean start and end time to weekdays.
        """
        fake_data = {
            datetime.date(2019, 3, 4): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2019, 3, 5): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
            datetime.date(2019, 3, 11): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }

        result = [
            [31500, 61650],
            [30600, 60300],
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
        ]

        self.assertEqual(result, utils.group_start_end_by_weekday(fake_data))

    def test_cache_decorator(self):
        """
        Test utils/cache result
        """
        moc = MagicMock()
        _func = lambda _: moc()
        cachelimit = 10

        wrapped = utils.cache(cachelimit)(_func)

        wrapped(1)
        wrapped(2)
        self.assertEqual(moc.call_count, 2)

        wrapped(1)
        self.assertEqual(moc.call_count, 2)

        with patch('presence_analyzer.utils.datetime') as dt:
            now = datetime.datetime.now()
            dt.now.return_value = now + datetime.timedelta(seconds=60)
            wrapped(1)
            self.assertEqual(moc.call_count, 3)

    def test_time_spent_by_day(self):
        """
        Test result of time_spent_by_day().
        """
        fake_data = {
            datetime.date(2019, 3, 4): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2019, 3, 5): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
            datetime.date(2019, 3, 11): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
        result_data = utils.time_spent_by_day(fake_data)

        result = [
            ['2019-03-04', 510],
            ['2019-03-05', 495],
            ['2019-03-11', 495]
        ]
        for _ in result:
            self.assertIn(_, result_data)


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
