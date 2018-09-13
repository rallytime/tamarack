# -*- coding: utf-8 -*-
'''
Contains functions required for interacting with Slack. The main function
used is the ``api_request`` function. This function handles the GET/POST
interactions to Slack.
'''

# Import Python libs
import json
import logging
import os

# Import Tornado libs
from tornado import gen
import tornado.httpclient


LOG = logging.getLogger(__name__)
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')


@gen.coroutine
def api_request(method='GET', headers=None, post_data=None):
    '''
    The main function used to interact with the Slack API. This function
    performs the actual requests to Slack when responding to various events.

    method
        Type of HTTP method. Defaults to ``GET``.

    headers
        HTTP Headers needed to make the request. Defaults to ``None``.

        Note: There are a couple of hard-coded defaults defined here presently.
        This is subject to change once configuration files or additional
        environment variables are defined. ``Content-Type`` defaults to
        ``application/json``, as required by Slack.

    post_data
        The data to pass to the Slack API request. Defaults to ``None``.

        This data will change based on the type of request made. For example,
        sending text to a Slack channel requires something like the following:
        ``'{"text": "My comment message."}'``. Other API calls may require
        different options and structures.

    '''
    if headers is None:
        headers = {'Content-Type': 'application/json'}

    data = None
    if post_data:
        data = json.dumps(post_data)
        data = data.encode('utf-8')

    http_client = tornado.httpclient.AsyncHTTPClient()
    request = tornado.httpclient.HTTPRequest(
        SLACK_WEBHOOK_URL,
        method=method,
        headers=headers,
        body=data
    )
    yield http_client.fetch(request)
