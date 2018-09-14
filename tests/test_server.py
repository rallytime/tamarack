# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.server.py
'''

# Import Python libs
from unittest.mock import MagicMock, patch
import pytest

# Import Tornado libs
import tornado.web

# Import Tamarack libs
import tamarack.server


@pytest.fixture(scope='module')
def preserve_globals(request):
    '''
    Test fixture used to preserve global variables
    '''
    hook_secret = tamarack.server.HOOK_SECRET_KEY
    gh_token = tamarack.server.GITHUB_TOKEN

    tamarack.server.HOOK_SECRET_KEY = None
    tamarack.server.GITHUB_TOKEN = None

    def restore_globals():
        '''
        Restore the previously defined global variables
        '''
        tamarack.server.HOOK_SECRET_KEY = hook_secret
        tamarack.server.GITHUB_TOKEN = gh_token

    request.addfinalizer(restore_globals)


class TestValidateGitHubSignature:
    '''
    TestCase for the validate_github_signature function.
    '''
    request = tornado.web.RequestHandler

    def test_incorrect_sha_type(self):
        '''
        Tests that an incorrect sha type returns False
        '''
        setattr(self.request, 'headers', {'X-Hub-Signature': 'foo=bar'})
        assert tamarack.server.validate_github_signature(self.request) is False

    def test_valid_signature(self, preserve_globals):  # pylint: disable=W0613,W0621
        '''
        Tests that a valid signature works and returns True
        '''
        test_key = 'superSecretTestingKey'
        tamarack.server.HOOK_SECRET_KEY = test_key
        setattr(self.request, 'headers',
                {'X-Hub-Signature': 'sha1=27a5d3cdd8ea4f3a3bcb5d807d44463191801509'})
        setattr(self.request, 'body', 'hello world'.encode('utf-8'))
        assert tamarack.server.validate_github_signature(self.request) is True


class TestCheckEnvVars:
    '''
    TestCase for the _check_env_vars function.
    '''

    def test_missing_hook_secret(self, preserve_globals):  # pylint: disable=W0613,W0621
        '''
        Tests that False is returned when the HOOK_SECRET_KEY is missing.
        '''
        tamarack.server.HOOK_SECRET_KEY = None
        assert tamarack.server._check_env_vars() is False

    def test_missing_gh_token(self, preserve_globals):  # pylint: disable=W0613,W0621
        '''
        Tests that False is returned when GITHUB_TOKEN is missing.
        '''
        tamarack.server.HOOK_SECRET_KEY = 'foo'
        assert tamarack.server._check_env_vars() is False

    def test_env_variables_present(self, preserve_globals):  # pylint: disable=W0613,W0621
        '''
        Tests that True is returned when all the required environment variables
        are present.
        '''
        tamarack.server.HOOK_SECRET_KEY = 'foo'
        tamarack.server.GITHUB_TOKEN = 'bar'
        assert tamarack.server._check_env_vars() is True


class TestSetupLogging:
    '''
    TestCase for the _setup_logging function.
    '''

    @patch('os.path.exists', MagicMock(return_value=False))
    def test_create_log_dir_failed(self):
        '''
        Tests that the log directory does not exists and couldn't be created.
        '''
        assert tamarack.server._setup_logging() is None

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('os.environ.get', MagicMock(return_value='foo'))
    def test_log_level_set_failed(self):
        '''
        Tests that a LOG_LEVEL environment variable was set, but at an incorrect level.
        '''
        assert tamarack.server._setup_logging() is None

    @patch('os.path.exists', MagicMock(return_value=True))
    def test_logging_success(self):
        '''
        Tests that logging was set up correctly.
        '''
        assert tamarack.server._setup_logging() is None

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('os.environ.get', MagicMock(return_value='WARN'))
    def test_success_valid_level(self):
        '''
        Tests that logging was set up correctly when passing a log_level.
        '''
        assert tamarack.server._setup_logging() is None
