# -*- coding: utf-8 -*-
'''
Tests for the functions in tamarack.server.py
'''

# Import Python libs
from unittest.mock import MagicMock, patch

# Import Tornado libs
import tornado.web

# Import Tamarack libs
import tamarack.server


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

    def test_valid_signature(self):
        '''
        Tests that a valid signature works and returns True
        '''
        test_key = 'superSecretTestingKey'
        tamarack.server.HOOK_SECRET_KEY = test_key
        setattr(self.request, 'headers',
                {'X-Hub-Signature': 'sha1=27a5d3cdd8ea4f3a3bcb5d807d44463191801509'})
        setattr(self.request, 'body', 'hello world'.encode('utf-8'))
        assert tamarack.server.validate_github_signature(self.request) is True

        # Reset variables for clean tests
        tamarack.server.HOOK_SECRET_KEY = None


class TestCheckEnvVars:
    '''
    TestCase for the _check_env_vars function.
    '''

    def test_missing_hook_secret(self):
        '''
        Tests that False is returned when the HOOK_SECRET_KEY is missing.
        '''
        assert tamarack.server._check_env_vars() is False

    def test_missing_gh_token(self):
        '''
        Tests that False is returned when GITHUB_TOKEN is missing.
        '''
        tamarack.server.HOOK_SECRET_KEY = 'foo'
        assert tamarack.server._check_env_vars() is False

        # Reset variable for clean tests
        tamarack.server.HOOK_SECRET_KEY = None

    def test_env_variables_present(self):
        '''
        Tests that True is returned when all the required environment variables
        are present.
        '''
        tamarack.server.HOOK_SECRET_KEY = 'foo'
        tamarack.server.GITHUB_TOKEN = 'bar'
        assert tamarack.server._check_env_vars() is True

        # Reset variables for clean tests
        tamarack.server.HOOK_SECRET_KEY = None
        tamarack.server.GITHUB_TOKEN = None


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
    @patch('os.environ.get', MagicMock(return_value='WARN'))
    def test_logging_success(self):
        '''
        Tests that logging was set up correctly.
        '''
        assert tamarack.server._setup_logging() is None
