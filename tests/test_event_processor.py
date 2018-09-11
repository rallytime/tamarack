# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.event_processor.py
'''

# Import Python libs
import os
import pytest

# Import Tornado libs
import tornado.testing
import tornado.web

# Import Tamarack libs
import tamarack.event_processor

GITHUB_TEST_TOKEN = os.environ.get('GITHUB_TEST_TOKEN') or ''


class TestHandleEvent(tornado.testing.AsyncTestCase):
    '''
    TestCase for the handle_event function
    '''

    @tornado.testing.gen_test
    def test_pull_request_event(self):
        '''
        Tests that a pull request event is handled
        '''
        event_data = {'number': 1,
                      'action': 'foo'}
        ret = yield tamarack.event_processor.handle_event(event_data, '')
        assert ret is None


class TestHandlePullRequest(tornado.testing.AsyncTestCase):
    '''
    TestCase for the handle_pull_request function
    '''

    @tornado.testing.gen_test
    def test_opened_pr(self):
        '''
        Tests that an opened pull request calls out to assign reviewers
        '''
        event_data = {'number': 1,
                      'action': 'opened',
                      'pull_request': {}}
        # PR #1 doesn't exist, so asserting against an HTTPError here is a fine way to
        # go without actually assigning a reviewer to a PR.
        with pytest.raises(tornado.web.HTTPError, message='Expecting a 500 Error from GitHub'):
            yield tamarack.event_processor.handle_pull_request(event_data, GITHUB_TEST_TOKEN)

    @tornado.testing.gen_test
    def test_merge_forward(self):
        '''
        Tests that an opened pull request that contains "Merge forward" in the
        title is ignored.
        '''
        event_data = {'number': 1,
                      'action': 'opened',
                      'pull_request': {'title': '[2018.3] Merge forward from 2017.7 to 2018.3'}}
        ret = yield tamarack.event_processor.handle_pull_request(event_data, '')
        assert ret is None

    @tornado.testing.gen_test
    def test_unknown_event(self):
        '''
        Tests that events other than "opened" are ignored.
        '''
        event_data = {'number': 1,
                      'action': 'foo'}
        ret = yield tamarack.event_processor.handle_pull_request(event_data, '')
        assert ret is None
