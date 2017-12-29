# -*- coding: utf-8 -*-
'''
The event processor handles incoming events and is called from server.py.
'''

# Import Tornado libs
from tornado import gen

# Import Tamarack libs
import tamarack.github
import tamarack.utils.prs


@gen.coroutine
def handle_event(event_data, token):
    '''
    An event has been received. Decide what to do with it.

    Presently, only pull requests are handled but this can be expanded later.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    if event_data.get('pull_request'):
        yield handle_pull_request(event_data, token)


@gen.coroutine
def handle_pull_request(event_data, token):
    '''
    Handles Pull Request events by examining the type of action that was triggered
    and then decides what to do next.

    For example, if a Pull Request is opened, the bot needs to comment on the pull
    request with the list of teams that should be reviewing the PR (if applicable).

    Currently this function only handles "opened" events for PRs and has the bot
    comment on the PR with the list of teams/users that should potentially review
    the submission. However, this can be easily expanded in the future.

    event_data
        Payload sent from GitHub.

    token
        GitHub user token.
    '''
    print('Received pull request event. Processing...')
    action = event_data.get('action')
    if action == 'opened':
        # Eventually we should move this to an "assign_reviewers" function,
        # but we need to wait for GitHub to expose this functionality for
        # team reviews. It will work for individual members, but not teams
        # presently. We could also loop through each team and request a
        # review from each individual member, but let's comment for now.
        yield tamarack.utils.prs.mention_reviewers(event_data, token)
    else:
        print('Skipping. Action is \'{0}\'. '
              'We only care about \'opened\'.'.format(action))
        return
