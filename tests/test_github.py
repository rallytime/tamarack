# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.github.py
'''

# Import Python libs
import os

# Import Tornado libs
import tornado.testing

# Import Tamarack libs
import tamarack.github

GITHUB_TEST_TOKEN = os.environ.get('GITHUB_TEST_TOKEN') or ''


class TestAPIRequest(tornado.testing.AsyncTestCase):
    '''
    TestCase for the api_request function
    '''

    @tornado.testing.gen_test
    def test_basic_get_request(self):
        '''
        Tests that a basic API call is made to GitHub with minimal information
        '''
        ret = yield tamarack.github.api_request(
            'https://api.github.com/repos/rallytime/tamarack/pulls/19',
            GITHUB_TEST_TOKEN)
        assert ret['title'] == 'Add first tests!'
