# -*- coding: utf-8 -*-
'''
Contains functions required for interacting with GitHub. The main function
used is the ``api_request`` function. This function handles the GET/POST
interactions to GitHub APIv3.
'''

# Import Python libs
import json
import logging

# Import Tornado libs
from tornado import gen
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web

LOG = logging.getLogger(__name__)


@gen.coroutine
def api_request(url, token, method='GET', headers=None, post_data=None):
    '''
    The main function used to interact with the GitHub API. This function
    performs the actual requests to GitHub when responding to various events.

    url
        The GitHub API url to make the request against.

    token
        GitHub user token.

    method
        Type of HTTP method. Defaults to ``GET``.

    headers
        HTTP Headers needed to make the request. Defaults to ``None``.

        Note: There are a couple of hard-coded defaults defined here presently.
        This is subject to change once configuration files or additional
        environment variables are defined. If headers is passed in, be aware
        that GitHub _requires_ that the ``User-Agent`` is set in addition to the
        ``Content-Type``.

    post_data
        The data to pass to the GitHub API request. Defaults to ``None``. This
        data will change based on the type of request made. For example, comments
        to issues/pull request require a ``'{"body": "My comment message."}'``
        structure, while other API calls require other options.

    '''
    if token:
        url = tornado.httputil.url_concat(url, {'access_token': token})

    if headers is None:
        headers = {'User-Agent': 'tamarack-bot',
                   'Content-Type': 'application/json'}

    body = None
    if post_data:
        body = json.dumps(post_data)
        body = body.encode('utf-8')

    http_client = tornado.httpclient.AsyncHTTPClient()
    request = tornado.httpclient.HTTPRequest(
        url,
        method=method,
        headers=headers,
        body=body,
    )
    response = yield http_client.fetch(request)
    return json.loads(response.body)
