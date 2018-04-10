# -*- coding: utf-8 -*-
'''
Main file that runs the tornado server for the bot.

Requires the HOOK_SECRET_KEY and GITHUB_TOKEN environment variables to be set.
Optionally, set the PORT environment variable as well. Default is ``8080``.

Requires Python 3.6.
'''

# Import Python libs
import hmac
import hashlib
import json
import logging
import os
import sys

# Import Tornado libs
from tornado import gen
import tornado.ioloop
import tornado.web
import tornado.httpclient

# Import Tamarack libs
import tamarack.event_processor

HOOK_SECRET_KEY = os.environ.get('HOOK_SECRET_KEY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

LOG = logging.getLogger(__name__)


class EventHandler(tornado.web.RequestHandler):
    '''
    Main handler for the "/events" endpoint
    '''
    def data_received(self, chunk):
        pass

    @gen.coroutine
    def post(self, *args, **kwargs):
        if not validate_github_signature(self.request):
            raise tornado.web.HTTPError(401)

        data = json.loads(self.request.body)
        yield tamarack.event_processor.handle_event(
            data, GITHUB_TOKEN
        )


def make_app():
    '''
    Create the tornado web application - uses the "events" endpoint.
    '''
    return tornado.web.Application([
        ('/events', EventHandler),
    ])


def validate_github_signature(request):
    '''
    Validate that the request coming in is from GitHub using the header
    signature.

    request
        The incoming request to validate.
    '''
    sha_type, gh_sig = request.headers.get('X-Hub-Signature').split('=')
    if sha_type != 'sha1':
        return False

    mac = hmac.new(HOOK_SECRET_KEY.encode('utf-8'),
                   msg=request.body, digestmod=hashlib.sha1)
    return hmac.compare_digest(mac.hexdigest(), gh_sig)


def _check_env_vars():
    check_ok = True

    if HOOK_SECRET_KEY is None:
        check_ok = False
        LOG.error(
            'The bot was started without a WebHook Secret Key.\n'
            'Please set the HOOK_SECRET_KEY environment variable.\n'
            'To get started:\n'
            '(1) Create a secret token.\n'
            '(2) Set the token in the "Secret" field of the bot\'s '
            'GitHub WebHook settings page.\n'
            '(3) Click "Update WebHook".\n'
            '(4) Set the token as an environment variable: '
            '"export HOOK_SECRET_KEY=your_secret_key".'
        )

    if GITHUB_TOKEN is None:
        check_ok = False
        LOG.error(
            'The bot was started without a GitHub authentication token.\n'
            'Please set the GITHUB_TOKEN environment variable: '
            '"export GITHUB_TOKEN=your_token".'
        )

    return check_ok


def _setup_logging():
    log_path = '/var/log/tamarack/tamarack.log'

    # Check if the logging directory exists and attempt to create it if necessary
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        LOG.info('Log directory not found. Trying to create it: %s', log_dir)
        try:
            os.makedirs(log_dir, mode=0o700)
        except OSError as err:
            LOG.error('Failed to create directory for log file: %s (%s)', log_dir, err)
            return

    # Set the log level, if provided. Otherwise, default to INFO
    log_level = os.environ.get('LOG_LEVEL', '').upper()
    if log_level:
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            LOG.error('Invalid log level: %s', log_level)
            return
    else:
        log_level = logging.INFO

    # Set up the basic logger config
    logging.basicConfig(
        filename=log_path,
        format='[%(levelname)s] %(message)s',
        level=log_level
    )

    # Add a StreamHandler to the logger to also stream logs to the console
    console = logging.StreamHandler()
    console.setLevel(log_level)
    logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    # First, set up logging.
    _setup_logging()

    # Check for mandatory settings.
    if _check_env_vars() is False:
        sys.exit()

    # Set the port, if provided. Otherwise default to 8080.
    PORT = os.environ.get('PORT')
    if PORT is None:
        PORT = 8080
        LOG.info('No PORT setting found. Using default at \'%s\'.', PORT)

    LOG.info('Starting Tamarack server.')
    LOG.info('Listening on port \'%s\'.', PORT)

    APP = make_app()
    APP.listen(PORT)
    tornado.ioloop.IOLoop.current().start()
