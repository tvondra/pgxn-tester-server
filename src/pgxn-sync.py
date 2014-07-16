#!/usr/bin/python

# This script performs a simple sync of users, releases and versions against the PGXN API (so we have locally in the DB).

import argparse
import httplib
import json
import os.path
import re
import shutil
import subprocess
import sys
import StringIO

import psycopg2
import psycopg2.extras

from pgxnclient import Spec
from pgxnclient.utils.semver import SemVer

from datetime import datetime

def parse_arguments():

	parser = argparse.ArgumentParser(description='PGXN Sync')

	parser.add_argument('-o', '--output', dest='output', default=None, metavar='FILENAME', type=str, help='JSON results file (default: results-YYYYMMDD-HHMI.json)')
	parser.add_argument('-a', '--api', dest='api', default='api.pgxn.org', help='API root URI (default: api.pgxn.org).')

	parser.add_argument('--host', dest='host', default='localhost', help='DB host (default: localhost)')
	parser.add_argument('--port', dest='port', default=5432, help='DB port (default: 5432)')
	parser.add_argument('--db',   dest='db',   required=True, help='DB name')
	parser.add_argument('--user', dest='user', default=os.getlogin(), help='DB user (default: %s)' % (os.getlogin(),))
	parser.add_argument('--password', dest='password', default=None, help='DB password (default: None)')

	return parser.parse_args()


def get_data(conn, uri):
	'a simple wrapper getting data for URI from an existing HTTP connection'

	# conn = httplib.HTTPConnection(host)
	conn.request("GET", uri)
	response = conn.getresponse().read()

	try:
		return json.loads(response)
	except Exception as ex:
		return None


def get_uri_templates(conn):
	'fetches the actual URI templates from the API root'

	return get_data(conn, '/index.json')


def get_users(conn, templates):
	'loops through all the letters and collects list of all users'

	users = []
	for letter in "abcdefghijklmnopqrstuvwxyz":
		uri = templates['userlist'].replace('{letter}', letter)
		tmp = get_data(conn, uri)
		if tmp is not None:
			users.extend(tmp)

	return users

def get_version_meta(conn, templates, release, version):

	uri = templates['meta'].replace('{dist}', release.lower()).replace('{version}', version['version'])
	return get_data(conn, uri)

def get_users_releases(conn, templates, user):
	'fetches list of releases for a single user'

	uri = templates['user'].replace('{user}', user)
	info = get_data(conn, uri)

	return info['releases']


def get_user_id(conn, user, name):

	try:

		cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cursor.execute('SELECT id FROM users WHERE user_name = %(user)s', {'user' : user})
		row = cursor.fetchone()

		if row:
			return row['id']

		cursor.execute('INSERT INTO users (user_name, full_name) VALUES (%(user)s, %(name)s)', {'user' : user, 'name' : name})
		cursor.execute("SELECT currval('users_id_seq') AS id")

		row = cursor.fetchone()

		return row['id']

	finally:

		cursor.close()


def get_release_id(conn, uid, release):

	try:

		cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cursor.execute('SELECT id FROM distributions WHERE dist_name = %(name)s', {'name' : release})
		row = cursor.fetchone()

		if row:
			return row['id']

		cursor.execute('INSERT INTO distributions (user_id, dist_name) VALUES (%(uid)s, %(name)s)', {'name' : release, 'uid' : uid})
		cursor.execute("SELECT currval('distributions_id_seq') AS id")

		row = cursor.fetchone()

		return row['id']

	finally:

		cursor.close()

def get_version_id(conn, rid, version, date, status, meta):

	try:

		cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cursor.execute('SELECT id FROM distribution_versions v WHERE dist_id = %(rid)s AND version_number = %(version)s', {'rid' : rid, 'version' : version})
		row = cursor.fetchone()

		if row:
			return row['id']

		cursor.execute('INSERT INTO distribution_versions (dist_id, version_number, version_date, version_status, version_meta) VALUES (%(rid)s, %(version)s, %(date)s, %(status)s, %(meta)s)', {'rid' : rid, 'version' : version, 'date' : date, 'status' : status, 'meta' : meta})
		cursor.execute("SELECT currval('distribution_versions_id_seq') AS id")

		row = cursor.fetchone()

		return row['id']

	finally:

		cursor.close()

def get_spec_url(host, release, version):
	return 'http://' + host + (templates['meta'].replace('{dist}', release).replace('{version}', version))

if __name__ == '__main__':

	# parse arguments first
	args = parse_arguments()

	# open connection to the database
	dbconn = psycopg2.connect(host=args.host, port=args.port, dbname=args.db, user=args.user)

	# open a HTTP connection to the API
	httpconn = httplib.HTTPConnection(args.api)

	# now get URI templates
	templates = get_uri_templates(httpconn)
	users = get_users(httpconn, templates)

	user_count = 0
	release_count = 0
	version_count = 0

	# test the releases for each user
	for user in users:

		# fetch list of releases for the user
		releases = get_users_releases(httpconn, templates, user['user'])

		# ignore users with no releases
		if len(releases) == 0:
			continue

		# make sure the user is in the database
		uid = get_user_id(dbconn, user['user'], user['name'])

		user_count += 1
		release_count += len(releases)

		# process all the user's releases
		for release in releases:

			rid = get_release_id(dbconn, uid, release)

			versions = []

			# collect versions from all three states
			for state in ['testing', 'unstable', 'stable']:
				if state in releases[release]:
					versions.extend({'date' : v['date'], 'version' : v['version'], 'state' : state} for v in releases[release][state])

			versions = sorted(versions, key = lambda x : x['date'], reverse=True)
			version_count += len(versions)

			# process all the versions for this release
			for version in versions:

				meta = get_version_meta(httpconn, templates, release, version)

				vid = get_version_id(dbconn, rid, version['version'], version['date'], version['state'], json.dumps(meta))

	dbconn.commit()

	print "SYNC users=%d releases=%d versions=%d" % (user_count, release_count, version_count)