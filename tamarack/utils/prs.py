# -*- coding: utf-8 -*-
'''
Handle any Tamarack Bot logic needed to perform tasks related to Pull Requests.
'''

# Import Python libs
import fnmatch
import logging

# Import Tornado libs
from tornado import gen
import tornado.web

# Import Tamarack libs
import tamarack.github

log = logging.getLogger(__name__)


@gen.coroutine
def mention_reviewers(event_data, token):
    '''
    Creates a comment on the pull request that mentions the affiliated code
    owners. The code owners are determined by getting a list of files that were
    changed in the pull request and comparing the list to the entries defined
    in the CODEOWNERS file.

    The comment then thanks the user for the pull request and mentions any
    matching code owners.

    If no matches are found, nothing is done.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    pr_owner = event_data.get('pull_request').get('user', {}).get('login')
    if pr_owner is None:
        raise tornado.web.HTTPError(
            500,
            'Pull Request owner could not be found.'
        )

    files = yield tamarack.github.get_pr_file_names(event_data, token)
    owners_contents = yield tamarack.github.get_owners_file_contents(
        event_data, token
    )
    owners = get_code_owners(files, owners_contents)
    if owners:
        if len(owners) == 1:
            names = owners[-1]
        else:
            names = ', '.join(owners[:-1])
            names += ', and {0}'.format(owners[-1])
        comment_txt = 'Hi @{0} - thank you for your pull request! Based on the ' \
                      'CODEOWNERS file in this repository, we identified {1} ' \
                      'to review this change.'.format(pr_owner, names)
        yield tamarack.github.create_pr_comment(
            event_data,
            token,
            comment_txt
        )


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
    pr_owner = event_data.get('pull_request').get('user', {}).get('login')
    if pr_owner is None:
        raise tornado.web.HTTPError(
            500,
            'Pull Request owner could not be found.'
        )
    files = yield tamarack.github.get_pr_file_names(event_data, token)
    owners_contents = yield tamarack.github.get_owners_file_contents(
        event_data, token
    )

    owners = get_code_owners(files, owners_contents)
    if owners:
        yield tamarack.github.assign_reviewers(
            event_data,
            token,
            owners
        )
    else:
        log.info(
            'No code owners were found for PR #%s. '
            'No reviewers requested.',
            event_data.get('number', 'unknown')
        )


def get_code_owners(files, owners_contents):
    '''
    Returns a list of code owners who should review a pull request.

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

    return matches
