# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.pull_request.py
'''

# Import Python libs
import pytest

# Import Tornado libs
import tornado.web

# Import Tamarack libs
import tamarack.pull_request


class TestGetPROwner:
    '''
    TestCase for the _get_pr_owner function
    '''

    def test_returned(self):
        '''
        Tests that the PR owner is returned correctly
        '''
        test_user = 'rallytime'
        assert tamarack.pull_request._get_pr_owner(
            {'pull_request': {'user': {'login': test_user}}}
        ) == test_user

    def test_raises_error(self):
        '''
        Tests that an error is raised when the PR owner is not found.
        '''
        with pytest.raises(tornado.web.HTTPError,
                           match='PR #1: Pull Request owner could not be found.'):
            tamarack.pull_request._get_pr_owner({'number': 1})


class TestGetURL:
    '''
    TestCase for the _get_url function
    '''
    url = 'http://foo.bar.com'
    mock_error_data = {'number': 1}

    def test_pr_type(self):
        '''
        Tests that a url is returned when passing in the "pull_request" url_type.
        '''
        event_data = {'pull_request': {'url': self.url}}
        assert tamarack.pull_request._get_url(event_data, 'pull_request') == self.url

    def test_error_pr_type(self):
        '''
        Tests that an error is raised when passing in the "pull_request" url_type
        and no PR URL is found.
        '''
        with pytest.raises(tornado.web.HTTPError,
                           match='PR #1: Pull Request URL could not be found.'):
            tamarack.pull_request._get_url(self.mock_error_data, 'pull_request')

    def test_repository_type(self):
        '''
        Tests that a url is returned when passing in the "repository" url_type.
        '''
        event_data = {'repository': {'url': self.url}}
        assert tamarack.pull_request._get_url(event_data, 'repository') == self.url

    def test_error_repository_type(self):
        '''
        Tests that an error is raised when passing in the "repository" url_type and
        no repository URL is found.
        '''
        with pytest.raises(tornado.web.HTTPError,
                           match='PR #1: Repository URL could not be found.'):
            tamarack.pull_request._get_url(self.mock_error_data, 'repository')

    def test_issue_url_type(self):
        '''
        Tests that a url is returned when passing in the "issue_url" url_type.
        '''
        event_data = {'pull_request': {'issue_url': self.url}}
        assert tamarack.pull_request._get_url(event_data, 'issue_url') == self.url

    def test_error_issue_type(self):
        '''
        Tests that an error is raised when passing in the "issue_url" url_type and
        no Issue URL is found.
        '''
        with pytest.raises(tornado.web.HTTPError,
                           match='PR #1: Issue URL could not be found.'):
            tamarack.pull_request._get_url(self.mock_error_data, 'issue_url')

    def test_general_error(self):
        '''
        Tests that an error is raised when passing in any other url_type that is not
        yet supported.
        '''
        with pytest.raises(tornado.web.HTTPError,
                           match='PR #1: URL could not be found.'):
            tamarack.pull_request._get_url(self.mock_error_data, 'foo')
