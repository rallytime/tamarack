# -*- coding: utf-8 -*-
'''
Main file that runs the tornado server for the bot.

Requires the HOOK_SECRET_KEY and GITHUB_TOKEN environment variables to be set.
Optionally, set the PORT environment variable as well. Default is ``8080``.

This requires a minimum version of Python 3.4. However, please note that this
project has only been tested with Python 3.6.
'''

# Import Python libs
import hmac
import hashlib
import json
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


class EventHandler(tornado.web.RequestHandler):
    '''
    Main handler for the "/events" endpoint
    '''
    def data_received(self, chunk):
        pass

    @gen.coroutine
    def post(self):
        if not validate_github_signature(self.request):
            raise tornado.web.HTTPError(401)

        data = json.loads(self.request.body)
        yield tamarack.event_processor.handle_event(
            data, GITHUB_TOKEN
        )


def make_app():
    return tornado.web.Application([
        ('/events', EventHandler),
    ])


def validate_github_signature(request):
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
        print('The bot was started without a WebHook Secret Key.')
        print('Please set the HOOK_SECRET_KEY environment variable.')
        print('To get started:')
        print('(1) Create a secret token.')
        print('(2) Set the token in the "Secret" field of the bot\'s '
              'GitHub WebHook settings page.')
        print('(3) Click "Update WebHook".')
        print('(4) Set the token as an environment variable: '
              '"export HOOK_SECRET_KEY=your_secret_key".')

    if GITHUB_TOKEN is None:
        check_ok = False
        print('The bot was started without a GitHub authentication token.')
        print('Please set the GITHUB_TOKEN environment variable: '
              '"export GITHUB_TOKEN=your_token".')

    return check_ok


if __name__ == '__main__':
    if _check_env_vars() is False:
        sys.exit()

    port = os.environ.get('PORT')
    if port is None:
        port = 8080
        print('No PORT setting found. Using default at \'{0}\'.'.format(port))
    print('Starting Tamarack server.')
    print('Listening on port \'{0}\'.'.format(port))
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
