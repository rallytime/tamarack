# -*- coding: utf-8 -*-
'''
Contains functions required for interacting with GitHub. The main function
used is the ``api_request`` function. This function handles the GET/POST
interactions to GitHub APIv3. Other functions in the file were written to
handle all kinds of GitHub API use cases.
'''

# Import Python libs
import base64
import json

# Import Tornado libs
from tornado import gen
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web


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


@gen.coroutine
def assign_reviewers(event_data, token, reviewers):
    '''
    Assign a reviewer (or list of reviewers) to a pull request.

    Note: Due to restrictions with the GitHub API, requesting a review from
    an organizational team is not permitted. This functionality should be
    exposed soon from GitHub, but for now it is limited to individual members
    of the organization.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.

    reviewers
        The single reviewer, or list of reviewers, to request a review from
        on the pull request.
    '''
    url = _get_pr_url(event_data)
    url += '/requested_reviewers'

    if not isinstance(reviewers, list):
        reviewers = [reviewers]

    teams = []
    individuals = []
    for reviewer in reviewers:
        if '/' in reviewer:
            org, team = reviewer.split('/')
            teams.append(team)
        else:
            individuals.append(reviewer)

    post_data = {}
    if individuals:
        post_data['reviewers'] = individuals
    if teams:
        post_data['team_reviewers'] = teams

    print(
        'Requesting reviewers {0} on pull request #{1}.'.format(
            reviewers,
            event_data.get('number', 'unknown')
        )
    )

    yield api_request(url, token, method='POST', post_data=post_data)


@gen.coroutine
def create_pr_comment(event_data, token, comment_txt):
    '''
    Creates a comment on a pull request with the provided text.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.

    comment_txt
        The text to post as the comment.
    '''
    url = event_data.get('pull_request', {}).get('issue_url')
    if url is None:
        raise tornado.web.HTTPError(
            500,
            'Pull Request URL could not be found.'
        )

    print('Posting comment to GitHub.')
    url += '/comments'

    yield api_request(url, token, method='POST', post_data={'body': comment_txt})


@gen.coroutine
def get_pr_file_names(event_data, token):
    '''
    Returns the list of changed files for a pull request.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    url = _get_pr_url(event_data)
    url += '/files'
    pr_num = event_data.get('number', 'unknown')

    print('PR #{0}: Fetching Pull Request file names.'.format(pr_num))
    response = yield api_request(url, token)

    file_names = []
    for item in response:
        file_names.append(item.get('filename'))

    print('PR #{0}: The following files names were found: {0}'.format(
        pr_num,
        file_names
    ))
    return file_names


@gen.coroutine
def get_owners_file_contents(event_data, token, branch=None):
    '''
    Returns the decoded content of the CODEOWNERS file.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.

    branch
        The name of the branch the CODEOWNERS file should be pulled from.
        Optional. If not provided, the base branch of the Pull Request
        will be used.
    '''
    url = event_data.get('repository', {}).get('url')
    if url is None:
        raise tornado.web.HTTPError(
            500,
            'Repository URL could not be found.'
        )
    url += '/contents/.github/CODEOWNERS'

    if branch is None:
        if event_data.get('pull_request'):
            branch = event_data.get('pull_request').get('base').get('ref')

    if branch:
        url += '?ref={0}'.format(branch)

    print('PR #{0}: Fetching CODEOWNERS file.'.format(
        event_data.get('number', 'unknown'))
    )
    contents = yield api_request(url, token)
    return base64.b64decode(contents.get('content')).decode('utf-8')


def _get_pr_url(event_data):
    '''
    Helper function to get the pull request url accurately.

    event_data
        Payload sent from GitHub.
    '''
    url = event_data.get('pull_request', {}).get('url')
    if url is None:
        raise tornado.web.HTTPError(
            500,
            'Pull Request URL could not be found.'
        )
    return url
