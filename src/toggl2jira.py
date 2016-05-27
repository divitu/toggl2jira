#!/usr/bin/env python

from __future__ import print_function

import argparse
from collections import namedtuple
from datetime import timedelta
import json
import os.path
import sys
import traceback
import urlparse

import dateutil.tz
from jira import JIRA
from oauthlib.oauth1 import SIGNATURE_RSA
from requests_oauthlib import OAuth1Session
from tabulate import tabulate

from toggl import TogglAPI, DateRange

SESSION_FILE = os.path.expanduser('~/.toggl2jira.session')
JIRA_DOMAIN = 'janrain.atlassian.net'
JIRA_SERVER = 'https://{}'.format(JIRA_DOMAIN)
REQUEST_TOKEN_URL = '{}/plugins/servlet/oauth/request-token'.format(JIRA_SERVER)
AUTHORIZE_URL = '{}/plugins/servlet/oauth/authorize'.format(JIRA_SERVER)
ACCESS_TOKEN_URL = '{}/plugins/servlet/oauth/access-token'.format(JIRA_SERVER)
TOGGL_KEY_FILE = os.path.expanduser('~/.toggl/api_key')

ticket_map = {
	'proserve':    'DEL-340',
	'devops':      'HO-3201',
	'cdc':         'PLAT-178',
	'engineering': 'ENG-778',
	'support':     'proserve',
	'ps':          'proserve',
	'sup':         'support',
	'ho':          'devops',
	'eng':         'engineering',
}

def main(argv=None):
	parser = argparse.ArgumentParser("Toggl -> JIRA")
	parser.add_argument("start_date")
	parser.add_argument("end_date", nargs='?')
	parser.add_argument("-v", "--verbose", action='store_true')
	args = parser.parse_args(argv)
	with open(TOGGL_KEY_FILE) as fh:
		toggl_api_key = fh.read().rstrip()

	try:
		dr = DateRange(args.start_date, args.end_date)
	except ValueError as err:
		print(err, file=sys.stderr)
		return 1

	toggl = TogglAPI(toggl_api_key)
	jira = connect_jira()

	while True:
		if args.verbose:
			print("Loading activity for {}".format(dr.dates))
		entries = toggl.get_time_entries(*dr.tuple())
		if entries:
			entries = process_entries(entries)
			break
		dr.decrement_day()

	entries.sort()

	output = [[human_date(e.date), e.ticket, e.duration, e.alias, e.message] for e in entries]
	print(tabulate(output, tablefmt='plain'))

	try:
		if raw_input("Type 'go' to approve the above worklog: ") != "go":
			return 0
	except KeyboardInterrupt:
		print()
		return 2

	for entry in entries:
		print("Adding {} to {}".format(entry.duration, entry.ticket))
		jira.add_worklog(entry.ticket, entry.duration, started=entry.date,
		                 comment=entry.message)
	return 0

def human_date(date):
	return date.astimezone(dateutil.tz.tzlocal()).strftime("%Y-%m-%d %H:%M")

def connect_jira():
	def make_jira(sess):
		return JIRA(JIRA_SERVER, oauth={'access_token': sess['oauth_token'],
		                                'access_token_secret': sess['oauth_token_secret'],
		                                'consumer_key': JIRA_CONSUMER_KEY,
		                                'key_cert': JIRA_PRIVATE_KEY})
	try:
		with open(SESSION_FILE) as fh:
			sess = json.load(fh)
		return make_jira(sess)
	except IOError: pass
	except:
		traceback.print_exc()
	oauth = OAuth1Session(JIRA_CONSUMER_KEY, signature_type='auth_header',
	                      signature_method=SIGNATURE_RSA, rsa_key=JIRA_PRIVATE_KEY, callback_uri='http://127.0.0.1/oauth-callback')
	oauth.fetch_request_token(REQUEST_TOKEN_URL)
	# if 'oauth_verifier' in request_token:
	print("Please visit the following URL to log in:")
	print(oauth.authorization_url(AUTHORIZE_URL))
	callback = raw_input("Paste the resulting url and press Enter to continue: ").decode('utf-8')
	verifier = urlparse.parse_qs(urlparse.urlparse(callback).query)['oauth_verifier'][0]
	access_token = oauth.fetch_access_token(ACCESS_TOKEN_URL, verifier)
	sess = {k: v for k, v in access_token.items()
	        if k in ['oauth_token', 'oauth_token_secret']}
	with open(SESSION_FILE, "w") as fh:
		json.dump(sess, fh)
	return make_jira(sess)

def make_entry(entry):
	pieces = entry.description.split(' ')
	name = pieces[0]
	ticket = name
	message = ' '.join(pieces[1:])
	while ticket in ticket_map:
		ticket = ticket_map[ticket]
	if name == ticket:
		name = ''
	return JIRAEntry(entry.start, ticket.upper(), hm(entry.duration), name, message)

def process_entries(entries):
	entries = [TogglEntry(e['description'], e['start'], e['duration']) for e in entries]
	jobs = {}
	for entry in entries:
		if entry.description not in jobs:
			jobs[entry.description] = entry
		else:
			jobs[entry.description].duration += entry.duration

	output = []
	for name, entry in jobs.iteritems():
		entry.duration = hmi(entry.duration)
		if entry.duration:
			output.append(make_entry(entry))
	return output

def hmi(s, round=15*60):
	result = ((s + round/2) // round) * round
	if result == 0 and s > round / 4:
		result = round
	return result

def hm(s):
	td = timedelta(seconds=s)
	h = td.days * 24 + td.seconds // 3600
	m = (td.seconds//60)%60
	result = '{}m'.format(m)
	if h > 0:
		result = '{}h {}'.format(h, result)
	return result

class TogglEntry(object):
	def __init__(self, description, start, duration):
		self.description = description
		self.start = dateutil.parser.parse(start)
		self.duration = duration

JIRAEntry = namedtuple('JIRAEntry', ['date', 'ticket', 'duration', 'alias', 'message'])

JIRA_CONSUMER_KEY = 'toggl2jira'

JIRA_PRIVATE_KEY = '''
-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDnWgIi5rLeR91a
8eVsNPruhTj+7ns5PSKb54a6NIrcuHFKOMmb/2qjh0s8TSTcvy+EY/nvTr2kduVq
CyN5llNNWT3hJ0NgUH75+xonF2Wt4a/+UhdR/+/pK6sPIajoy/LahoJ4hAGhUTBB
cn7oWNvVuBVfLTyX3DObI10EZNeh9I5g3iC30WCymap9ngkERnDqkJoDlo4Zppwb
ASgVS0ZBmf8AYr2IfpH/cvoCTp8PySw9Iv8G8YJnudKk0ybFoeamamzBcffpgNEH
ebfsbrEHxsmnaC8WTSYw7RN65YIIJnTBxNjWoFwpb1UJmwYY0jteeeHUvBnqqAi0
MaiK/F0hAgMBAAECggEBAObIgxkNyaCzT71JUPOAZlFJ1HF6tLGEquGbNGrLvzov
Q9Qmkfdr85Ttgb/FtOAAWAZZNRnkEondkT0Xn2vK6Y5fV7siz7NkmUYFlzEnxeaP
HGE2wsyp40lWpm2Rxk10Je6X/8744CdsNhcTgEWHXsTzvV4UYj2bDF/WBxQ7BGAp
D9H7lCtG2ppPIvOV2zX3j8EpDY6iWoR9KLGWDwnPth5h0TnpVEKENLzXayRvtWrQ
H32n1itEwS0vR/OFV6ps8V+pejTB0BWJlIdK41mHk/9nnvJeOMo+ubmmGsw3TM6L
Tabwd/Cit5TgBn8/8CBSApzWuMrrPpGxN8Npy8KBSAECgYEA9Plo3XXkVyNjfOFF
qhX7iWaRkJKjZrBZLiGRMVsoLDH6BDB8FPUwGtkl8X9PoB4mSXMgtOUAoMuRAx2N
fNWKmvl7DzIAgSE/KOimNx07X7aIK0zH0v42XEiV+DIky7GvYB+RF950rT80qlrr
Vca8cYGvMPMIFvKac+VlV4EiFVkCgYEA8cOjef1HG/mO583+mAYnC2GwydF/lgeY
r9PZuDMwAjKd6emcK9mB4AbNMKA2Z7iZsr4zlR2zTq5jvzpIQF5XmBASeaLBg/km
jR0S/djueMLqCyShcZ0SYy/D6tgoPgVsUbYiFwzd9h8kITmAAyWX2Dbprp6mEMO9
GQzRhR4Z5QkCgYEA3wo53PCajm/NBAVC3UIYe5gkTmIEXdmPyL2NKUfawqpZ/Ph7
8MTwIHG25zLHt3vb1iH5FFowATZ2eESu7oqqIMGmtkYLSYaQr9lqhGGcDl/tiKbm
hIcpzUnVKV3WPJMxnq3+96F1z8rtU3FmNPm11w6BCGst4V7PG1gvtcT/2DkCgYBq
1SjIH0Ps+LpNdJmsVAus295jUFAw2+p8yADNhNESJ4vgcXqxZcweUuMZObLQ4qII
ekQRAK7bdfRd7ENBLm9GotOHLISW7OI8OTzLL7Exa/BAPE+bBO27JsBMZnhh78ON
2A34YZczy08L33zR5yrSQHHC2BhKEDTffOqZCFQpAQKBgQCip9irWCzEEk88vwbl
ZcsMB8cYxADaUXRvQBJek1fiysaQEAvkc+IIrU6vXNMIaRMk1GIZ4hcn8w/olP0w
1FMXjYhA5O2Z6CC5IVr+JeLh4rL9hyfUcf1SQ4YsSatLziU3SoyWvdQZBG1vM69v
E0fHSd6f1ClyEi3c1NK049TU9A==
-----END PRIVATE KEY-----
'''

if __name__ == '__main__':
	code = main()
	if code:
		exit(code)
