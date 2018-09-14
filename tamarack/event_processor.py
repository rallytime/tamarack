# -*- coding: utf-8 -*-
'''
The event processor handles incoming events and is called from server.py.
'''

# Import Python libs
import logging

# Import Tornado libs
from tornado import gen

# Import Tamarack libs
import tamarack.github
import tamarack.pull_request
import tamarack.slack

LOG = logging.getLogger(__name__)


@gen.coroutine
def handle_event(event_data, token):
    '''
    An event has been received. Decide what to do with it.

    Presently, only pull requests are handled. However, this can be expanded
    later.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    if event_data.get('pull_request'):
        yield handle_pull_request(event_data, token)
    elif event_data.get('ref_type'):
        yield handle_create_event(event_data)


@gen.coroutine
def handle_pull_request(event_data, token):
    '''
    Handles Pull Request events by examining the type of action that was triggered
    and then decides what to do next.

    For example, if a Pull Request is opened, the bot needs to assign reviewers to
    the pull request with the list of teams that should be reviewing the pull
    request, if applicable.

    Currently this function only handles "opened" events for PRs and has the bot
    assign reviewers to the PR with the list of teams/users that should review
    the submission. However, this can be easily expanded in the future.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    pr_num = event_data.get('number', 'unknown')
    action = event_data.get('action', 'unknown')

    LOG.info('PR #%s: Received pull request event. Processing...', pr_num)

    # Assign reviewers on "opened" PRs, as applicable.
    if action == 'opened':
        # Skip Merge Forward PRs
        if 'Merge forward' in event_data.get('pull_request', {}).get('title', ''):
            LOG.info('PR #%s: Skipping. PR is a merge-forward. Reviewers are not '
                     'assigned to merge-forward PRs via Tamarack.', pr_num)
            return

        # Assign reviewers!
        yield tamarack.pull_request.assign_reviewers(event_data, token)
    else:
        LOG.info('PR #%s: Skipping. Action is \'%s\'. We only care about '
                 '\'opened\'.', pr_num, action)
        return


@gen.coroutine
def handle_create_event(event_data):
    '''
    Handles Create events by examining the type of reference object that was
    created and then decides what to do next.

    For example, if a new branch is pushed to the repository, the bot needs to
    send a slack message to the configured Slack App Webhook URL.

    event_data
        Payload sent from GitHub.

    '''
    event_type = event_data.get('ref_type')
    ref_name = event_data.get('ref')

    LOG.info('Received create event. Processing...')

    # Send message to Slack when new branch is created.
    if event_type == 'branch':
        LOG.info('New branch \'%s\' was created in GitHub. Posting to Slack.', ref_name)
        post_data = {'attachments': [
            {'color': 'good',
             'fields': [{
                 'value':
                     'A new branch named `{0}` was created in the Salt repo.'.format(
                         ref_name
                     )
                 }]}
        ]}

        yield tamarack.slack.api_request(
            method='POST',
            post_data=post_data
        )
    else:
        LOG.info('Skipping. Create event is of \'%s\' type. We only care about '
                 '\'branch\'.', event_type)
        return
