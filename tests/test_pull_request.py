# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.pull_request.py
'''

# Import Python libs
import pytest
from unittest.mock import MagicMock, patch

# Import Tornado libs
import tornado.concurrent
import tornado.httpclient
import tornado.testing
import tornado.web

# Import Tamarack libs
import tamarack.pull_request


class TestGetCodeOwners:
    '''
    TestCase for the _get_code_owners function
    '''
    owners_content = '# SALTSTACK CODE OWNERS\n' \
                     '\n' \
                     '# Team State\n' \
                     'salt/state.py       @saltstack/team-state\n' \
                     '\n' \
                     '# Team Core\n' \
                     'salt/auth/*         @saltstack/team-core\n'

    def test_no_matches(self):
        '''
        Tests that no code owners are found
        '''
        assert tamarack.pull_request._get_code_owners(
            ['foo/bar.py'],
            self.owners_content
        ) == []

    def test_matches_found(self):
        '''
        Tests that code owners are found for a simple owners file
        '''
        assert tamarack.pull_request._get_code_owners(
            ['salt/state.py'],
            self.owners_content
        ) == ['@saltstack/team-state']

    def test_core_and_suse_matches(self):
        '''
        Tests that team-suse is requested for a review whenever team-core is
        requested for a review whenever team-core is.
        '''
        assert tamarack.pull_request._get_code_owners(
            ['salt/auth/pki.py'],
            self.owners_content
        ) == ['@saltstack/team-core', '@saltstack/team-suse']


class TestGetOwnersFileContents(tornado.testing.AsyncTestCase):
    '''
    TestCase for the get_owners_file_contents function
    '''

    @tornado.testing.gen_test
    def test_owners_file_contents_found_with_branch(self):
        '''
        Tests that the owners file contents are returned when a branch is passed.
        '''
        event_data = {'number': 49517,
                      'repository':
                          {'url': 'https://api.github.com/repos/saltstack/salt'},
                      'pull_request': {'base': {'ref': 'develop'}}}
        contents = yield tamarack.pull_request.get_owners_file_contents(
            event_data, ''
        )
        assert '# Lines starting with \'#\' are comments.' in contents
        assert 'salt/cloud/*                        @saltstack/team-cloud' in contents
        assert 'tests/*/test_reg.py                 @saltstack/team-windows' in contents

    @tornado.testing.gen_test
    def test_owners_file_contents_found_no_branch(self):
        '''
        Tests that the owners file contents are returned when a branch is not passed.
        '''
        event_data = {'number': 49517,
                      'repository':
                          {'url': 'https://api.github.com/repos/saltstack/salt'}}
        contents = yield tamarack.pull_request.get_owners_file_contents(
            event_data, '', branch='2018.3'
        )
        assert '# Team State' in contents
        assert 'salt/state.py                       @saltstack/team-state' in contents
        assert 'salt/cli/ssh.py                     @saltstack/team-ssh' in contents


class TestGetPRFileNames(tornado.testing.AsyncTestCase):
    '''
    TestCase for the get_pr_file_names function
    '''

    @tornado.testing.gen_test
    def test_files_found(self):
        '''
        Tests that a list of files are found and returned
        '''
        event_data = {'number': 49517,
                      'pull_request':
                          {'url': 'https://api.github.com/repos/saltstack/salt/pulls/49517'}}
        files = yield tamarack.pull_request.get_pr_file_names(event_data, '')
        assert files == ['salt/modules/yumpkg.py']


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
