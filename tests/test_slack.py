# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.slack.py
'''

# Import Tornado libs
import tornado.testing

# Import Tamarack libs
import tamarack.slack


class TestAPIRequest(tornado.testing.AsyncTestCase):
    '''
    TestCase for the api_request function
    '''

    @tornado.testing.gen_test
    def test_request_no_data(self):
        '''
        Tests that a basic API call is made to Slack with minimal information
        '''
        slack_url = tamarack.slack.SLACK_WEBHOOK_URL
        tamarack.slack.SLACK_WEBHOOK_URL = 'https://slack.com/api/api.test'
        ret = yield tamarack.slack.api_request(
            method='POST',
            post_data={'text': 'foo'}
        )
        assert ret is None

        # Reset variables for clean tests
        tamarack.slack.SLACK_WEBHOOK_URL = slack_url
