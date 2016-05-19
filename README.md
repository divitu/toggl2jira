Prerequisites
=============

Get a Toggl API key for your account and put it in `~/.toggl/api_key`.

Clone and install `toggl-api`

    git clone git@github.com:divitu/toggl-api.git
    cd toggl-api
    ./setup.py develop

Installation
============

Save `toggl2jira.py` somewhere.  Make sure you have permission to read and execute it.

Usage
=====

`./toggl2jira.py` to scan Toggl for a day's work.  If no date is supplied, defaults to today.
If a date has no work, runs again for previous day.  Uses `dateparser` so it understands some
human-friendly terms such as "yesterday".
