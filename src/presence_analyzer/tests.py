# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from mock import patch

from presence_analyzer import main, utils, views


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

MALF_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'malformed_data.csv'
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
        Test presence start and end time by weekday for user that is not in data.
        """
        resp = self.client.get('/api/v1/presence_start_end/1')
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

    @patch.dict('presence_analyzer.main.app.config', {'DATA_CSV': MALF_DATA_CSV})
    @patch('presence_analyzer.utils.log')
    def test_malformed_get_data(self, mock_log):
        """
        Test get_data() with malformed data.
        """
        utils.get_data()
        self.assertTrue(mock_log.debug.called)

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
            utils.interval(datetime.time(11, 30, 0), datetime.time(12, 30, 0))
        )
        self.assertEqual(
            0,
            utils.interval(datetime.time(7, 7, 7), datetime.time(7, 7, 7))
        )
        self.assertEqual(
            86399,
            utils.interval(datetime.time(0, 0, 0), datetime.time(23, 59, 59))
        )
        self.assertEqual(
            3539,
            utils.interval(datetime.time(12, 59, 59), datetime.time(13, 58, 58))
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
