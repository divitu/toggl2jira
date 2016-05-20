Prerequisites
=============

Get a Toggl API key for your account and put it in `~/.toggl/api_key`.

Clone and install `toggl-api`

    git clone git@github.com:divitu/toggl-api.git
    cd toggl-api
    ./setup.py develop

Installation
============

    git clone git@gist.github.com:5f849db6bba401583e1758b90abf301b.git toggl2jira

Usage
=====

`./toggl2jira.py` to scan Toggl for a day's work.  If no date is supplied, defaults to today.
If a date has no work, runs again for previous day.  Uses `dateparser` so it understands some
human-friendly terms such as "yesterday".

Upon first usage, and occasionally thereafter, you will be prompted to go through a silly
OAuth login dance.

At the prompt, type "go" to load the work into JIRA.
