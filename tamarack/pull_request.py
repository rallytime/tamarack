# -*- coding: utf-8 -*-
'''
Handles common Pull Request tasks.
'''

# Import Python libs
import base64
import fnmatch
import logging

# Import Tornado libs
from tornado import gen
import tornado.web

# Import Tamarack libs
import tamarack.github

LOG = logging.getLogger(__name__)


@gen.coroutine
def assign_reviewers(event_data, token):
    '''
    Assigns reviewers on the pull request to the affiliated code owners. The code
    owners are determined by getting a list of files that were changed in the pull
    request and comparing the list to the entries defined in the CODEOWNERS file.

    If no matches are found, nothing is done.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    pr_num = event_data.get('number', 'unknown')

    files = yield get_pr_file_names(event_data, token)
    owners_contents = yield get_owners_file_contents(
        event_data, token
    )

    reviewers = _get_code_owners(files, owners_contents)
    if not reviewers:
        LOG.info('PR #%s: No code owners were found, no reviewers requested.',
                 pr_num)
        return

    url = _get_url(event_data, 'pull_request')
    url += '/requested_reviewers'

    if not isinstance(reviewers, list):
        reviewers = [reviewers]

    teams = []
    individuals = []
    for reviewer in reviewers:
        if '/' in reviewer:
            _, team = str(reviewer).split('/')
            teams.append(team)
        else:
            individuals.append(reviewer)

    post_data = {}
    if individuals:
        post_data['reviewers'] = individuals
    if teams:
        post_data['team_reviewers'] = teams

    LOG.info('PR #%s: Requesting reviewers %s.',
             pr_num, reviewers)

    yield tamarack.github.api_request(
        url,
        token,
        method='POST',
        post_data=post_data
    )


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
    url = _get_url(event_data, 'repository')
    url += '/contents/.github/CODEOWNERS'

    if branch is None:
        if event_data.get('pull_request'):
            branch = event_data.get('pull_request').get('base').get('ref')

    if branch:
        url += '?ref={0}'.format(branch)

    LOG.info('PR #%s: Fetching CODEOWNERS file.',
             event_data.get('number', 'unknown'))

    contents = yield tamarack.github.api_request(url, token)
    return base64.b64decode(contents.get('content')).decode('utf-8')


@gen.coroutine
def get_pr_file_names(event_data, token):
    '''
    Returns the list of changed files for a pull request.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    pr_num = event_data.get('number', 'unknown')
    url = _get_url(event_data, 'pull_request')
    url += '/files'

    LOG.info('PR #%s: Fetching Pull Request file names.', pr_num)
    response = yield tamarack.github.api_request(url, token)

    file_names = []
    for item in response:
        file_names.append(item.get('filename'))

    LOG.info('PR #%s: The following file names were found: %s',
             pr_num, file_names)
    return file_names


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
    url = _get_url(event_data, 'issue_url')

    LOG.info('PR #%s: Posting comment to GitHub.', event_data.get('number', 'unknown'))
    url += '/comments'

    yield tamarack.github.api_request(
        url,
        token,
        method='POST',
        post_data={'body': comment_txt}
    )


def _get_code_owners(files, owners_contents):
    '''
    Helper function that returns a list of code owners who should review a pull
    request.

    files
        The list of pull request files to find owners for.

    owners_contents
        The contents of the CODEOWNERS file.
    '''
    # Filter contents of the owners file. Ignore comments and blank lines.
    entries = []
    for line in owners_contents.splitlines():
        if not line:
            continue
        elif line.startswith('#'):
            continue
        # define ownership entries as a list of tuples
        file_name, owner = line.split()
        entries.append((file_name, owner))

    # Search through PR files to find ownership matches
    matches = []
    for entry in entries:
        for item in files:
            if fnmatch.fnmatch(item, entry[0]):
                matches.append(entry[1])

                # SUSE wants to review any PRs the Core team reviews.
                # Instead of duplicating the CODEOWNERS file, handle
                # this programmatically here - See Issue #14.
                if 'team-core' in entry[1]:
                    matches.append('@saltstack/team-suse')

    return matches


def _get_pr_owner(event_data):
    '''
    Helper function to handle getting the pull request owner from the event_data.

    event_data
        Payload sent from GitHub.
    '''
    pr_owner = event_data.get('pull_request').get('user', {}).get('login')
    if pr_owner is None:
        raise tornado.web.HTTPError(
            500,
            'PR #%s: Pull Request owner could not be found.',
            event_data.get('number', 'unknown')
        )
    return pr_owner


def _get_url(event_data, url_type):
    '''
    Helper function to get a GitHub url based on the type provided.

    event_data
        Payload sent from GitHub.

    type
        The type of GitHub URL type. ``pull_request`` and ``repository`` are
        supported.
    '''
    url = None
    if url_type == 'pull_request':
        url = event_data.get('pull_request', {}).get('url')
        url_type = 'Pull Request URL'
    elif url_type == 'repository':
        url = event_data.get('repository', {}).get('url')
        url_type = 'Repository URL'
    elif url_type == 'issue_url':
        url = event_data.get('pull_request', {}).get('issue_url')
        url_type = 'Issue URL'
    else:
        url_type = 'URL'

    if url is None:
        raise tornado.web.HTTPError(
            500,
            'PR #%s: %s could not be found.',
            event_data.get('number', 'unknown'), url_type
        )
    return url
