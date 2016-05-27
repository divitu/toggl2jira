Prerequisites
=============

Get a Toggl API key for your account and put it in `~/.toggl/api_key`.

Installation
============

    git clone git@github.com:divitu/toggl2jira.git
    cd toggl2jira
    ./setup.py develop

Upgrading
=========

    cd toggl2jira
    git pull --no-edit

Usage
=====

`toggl2jira` to scan Toggl for days' work.  If no date is supplied, defaults to
today.  If a single date has no work, runs again for previous day.  Uses
`dateparser` so it understands some human-friendly terms such as "yesterday".

Upon first usage, and occasionally thereafter, you will be prompted to go
through a silly OAuth login dance.

At the prompt, type "go" to load the work into JIRA.
