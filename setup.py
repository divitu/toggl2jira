#!/usr/bin/env python

from setuptools import setup

setup(
	name='toggl2jira',
	description='Worklog loader from Toggl to Jira',
	author='Colin von Heuring',
	author_email='colin@von.heuri.ng',
	install_requires=['jira', 'python-dateutil', 'requests', 'tabulate',
	                  'toggl-api'],
	scripts=['scripts/toggl2jira'],
)
