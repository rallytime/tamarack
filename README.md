[![Build Status](https://travis-ci.org/rallytime/tamarack.svg?branch=master)](https://travis-ci.org/rallytime/tamarack)
[![Coverage Status](https://coveralls.io/repos/github/rallytime/tamarack/badge.svg?branch=master&service=github)](https://coveralls.io/github/rallytime/tamarack?branch=master)

# Tamarack

A bot built with Python Tornado to automate common pull request tasks.

Specifically designed for use with the [Salt repository](https://github.com/saltstack/salt).

**WARNING**: This project is very new and subject to change without notice.

This bot listens for pull request events coming from GitHub and responds to them as needed.

The first task this bot was written to do was to analyze newly opened Pull Requests and check
if the files changed match any of the entries in the `CODEOWNERS` file. If any matches are
found, the bot will comment on the Pull Request and mention the matching owners.

## Dependencies

Tamarack requires a minimum version of:
- Python 3.6
- [GitHub APIv3](https://developer.github.com/v3/)
- Tornado >= 4.5.2, < 5.0

## Set Up

1. Clone this repo
1. Install Tornado
1. Configure GitHub Webhooks
1. Set environment variables
1. Run the server

### GitHub Webhooks

To configure a web hook, navigate to the project's settings page and click on the `Webhooks`
section. Complete the following:
- Payload URL: (https://your-tamarack-server.com/events)
- Content type: application/json
- Secret: your-secret (see HOOK_SECRET_KEY information below)
- Select the "Let me select individual events." radio button, then check `Pull request`.

Then, click `Add Webhook`.

**NOTE**: Tamarack presently only cares about payloads that come to the `/events` endpoint.
Please be sure that `/events` is at the end of the `Payload URL` setting.

### Environment Variables

Tamarack needs a couple of configurations to be in place before it can start reacting to Pull
Request events from GitHub. The following environment variables must be set:

- GITHUB_TOKEN
- HOOK_SECRET_KEY
- PORT (optional)

#### GitHub Token

The `GITHUB_TOKEN` is the API token Tamarack will use to interact with the GitHub API. This token
should be generated on the GitHub account that the bot will run as, comment on pull requests, etc.

To get started:
1. Generate an API access token [here](https://github.com/settings/tokens).
1. Set the token as an environment variable:
```
export GITHUB_TOKEN=your_github_token
```

#### Hook Secret Key

The `HOOK_SECRET_KEY` is generated on GitHub's WebHook settings page. This secret key is needed to
limit requests to the `/events` endpoint only to payloads coming from GitHub. 

To get started:

1. Create a secret token at the CLI, using high entropy.
1. Set the token in the 'Secret' field of the bot's GitHub WebHook settings page.
1. Click 'Update WebHook'.
1. Set the token as an environment variable:
```
export HOOK_SECRET_KEY=your_secret_key
```

#### Port

The `PORT` environment variable configures the port that Tamarack uses. This variable is optional.
The default is set to `8080`. To use a different port, set the environment variable:
```
export PORT=1234
```

### Running Tamarack

Once the GitHub web hook is arranged and the environment variables are set, it is now time to run
the server:

```
python server.py
```

The server should be listening for events coming from GitHub and responding to them appropriately.

## Development

When testing new features and code changes for Tamarack, it is a good idea to set up some personal
GitHub API tokens, a web hook on your own repository, and to run Tamarack in a virtual environment.

[ngrok](https://ngrok.com/) can be used to easily expose a local server to use as your web hook URL
for payloads.

Simply place the URL that ngrok gave you when you started it in the `Payload URL` section of your
Web hook settings and save the changes. (Remember to place `/events` at the end of the URL.) Then
restart Tamarack.

The payload URL will look something like this:
```
http://12345678.ngrok.io/events
```
