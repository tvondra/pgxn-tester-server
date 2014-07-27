import flask
from flask import request
from flask.ext.restful import Resource, abort, reqparse

from db import DB
from utils import verify_signature, get_pg_version
import uuid
import base64

def result_parser():

	result_parser = reqparse.RequestParser()
	result_parser.add_argument('distribution', type=str, required=True, location='json')
	result_parser.add_argument('version', type=str, required=True, location='json')
	result_parser.add_argument('machine', type=str, required=True, location='json')
	result_parser.add_argument('signature', type=str, required=True, location='json')
	result_parser.add_argument('load', type=str, location='json')
	result_parser.add_argument('install', type=str, location='json')
	result_parser.add_argument('check', type=str, location='json')
	result_parser.add_argument('install_log', type=str, location='json')
	result_parser.add_argument('install_duration', type=int, location='json')
	result_parser.add_argument('load_log', type=str, location='json')
	result_parser.add_argument('load_duration', type=int, location='json')
	result_parser.add_argument('check_log', type=str, location='json')
	result_parser.add_argument('check_duration', type=int, location='json')
	result_parser.add_argument('check_diff', type=str, location='json')
	result_parser.add_argument('config', type=str, location='json')
	result_parser.add_argument('env', type=str, location='json')
	result_parser.add_argument('uuid', type=str, location='json')

	return result_parser

class ResultList(Resource):

	# FIXME implement proper paging (using submit_date)

	# basic list of results with basic info (no detailed logs)
	# TODO consider showing only the last test from each machine/version/release (who cares if it failed before, when it passes now)
	list_sql = """SELECT result_uuid AS uuid, user_name AS user, dist_name AS dist, m.name AS machine, isodate(submit_date) AS test_date,
						 version_number AS version, isodate(version_date) AS version_date, version_status AS status, pg_version,
						 install_result AS install, load_result AS load, check_result AS "check"
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)
										 JOIN results r ON (r.dist_version_id = v.id)
										 JOIN machines m ON (r.machine_id = m.id)"""

	def get(self):
		'get info about distribution, along with info about author'

		# TODO add some basic paging of results (using submit_date of the results)
		where = []
		params = {}

		if 'page' in request.args:
			params.update({'offset' : int(request.args['page']) * 20})
		else:
			params.update({'offset' : 0})

		# filter only distributions published by the particular user
		if 'user' in request.args:
			where.append('user_name = %(user)s')
			params.update({'user' : request.args['user']})

		# filter only results submitted by the particular machine
		if 'machine' in request.args:
			where.append('m.name = %(machine)s')
			params.update({'machine' : request.args['machine']})

		# filter results by distribution 
		if 'distribution' in request.args:
			where.append('dist_name = %(distribution)s')
			params.update({'distribution' : request.args['distribution']})

		# filter results by version
		if 'version' in request.args:

			# this is valid only if 'distribution' parameter is provided too
			if 'distribution' not in request.args:
				abort(400, "when providing 'version' parameter, 'distribution' is required")

			where.append('version_number = %(version)s')
			params.update({'version' : request.args['version']})

		# filter results by PostgreSQL major version
		if 'pg' in request.args:
			where.append('major_version(pg_version) = %(pg)s')
			params.update({'pg' : request.args['pg']})

		# filter results by distribution status
		if 'status' in request.args:
			where.append('version_status = %(status)s')
			params.update({'status' : request.args['status']})

		# filter by PostgreSQL version
		if 'pg_version' in request.args:
			where.append('pg_version = %(pgversion)s')
			params.update({'pgversion' : request.args['pg_version']})

		# paging (using the submit_date + LIMIT)
		if 'date' in request.args:
			where.append('submit_date <= %(date)s')
			params.update({'date' : request.args['date']})

		# filter by install result
		if 'install' in request.args:
			where.append('install_result = %(install)s')
			params.update({'install' : request.args['install']})

		# filter by load result
		if 'load' in request.args:
			where.append('load_result = %(load)s')
			params.update({'load' : request.args['load']})

		# filter by check result
		if 'check' in request.args:
			where.append('check_result = %(check)s')
			params.update({'check' : request.args['check']})

		sql = ResultList.list_sql
		if where:
			sql += ' WHERE ' + (' AND '.join(where))

		sql += " ORDER BY submit_date DESC LIMIT 20 OFFSET %(offset)s"

		with DB() as (conn, cursor):
			# info about distribution
			cursor.execute(sql, params)
			results = cursor.fetchall()

		return results

	def post(self):

		# FIXME implement some sort of size limits, i.e. no results over 1MB or something like that
		# FIXME implement some sort of rate limits, i.e. no client can submit over 1000 results per hour or something like that

		args = result_parser().parse_args()

		# fetch info about the machine
		with DB() as (conn, cursor):
			
			cursor.execute('SELECT id, secret_key FROM machines WHERE name = %(name)s AND is_approved AND is_active', {'name' : args.machine})
			machine = cursor.fetchone()

			if not machine:
				abort(401, message="unknown / inactive machine")

			# verify the signature
			if not verify_signature(args, secret=machine['secret_key'], signature=args.signature):
				abort(401, message='invalid signature')

			cursor.execute('SELECT v.id AS id FROM distribution_versions v JOIN distributions d ON (d.id = v.dist_id) WHERE dist_name = %(name)s AND version_number = %(version)s',
							{'name' : args.distribution, 'version' : args.version})
			version = cursor.fetchone()

			if not version:
				abort(401, message="unknown distribution/version")

			# check that we haven't seen the UUID before (this means someone bad can't replay the message over and over)
			cursor.execute('SELECT result_uuid AS uuid FROM results WHERE result_uuid = %(uuid)s LIMIT 1', {'uuid' : args.uuid})
			result = cursor.fetchone()

			if result:
				abort(401, message="duplicate uuid")

		# OK, so the submitted result seems to be OK ... let's store the data
		with DB(False) as (conn, cursor):
			
			cursor.execute('''INSERT INTO results (result_uuid, machine_id, dist_version_id, pg_version, pg_config, env_info, load_result, install_result, check_result,
												   load_duration, install_duration, check_duration, log_load, log_install, log_check, check_diff)
							  VALUES (%(uuid)s, %(machine)s, %(version)s, %(pgversion)s, %(config)s, %(env)s, %(load)s, %(install)s, %(check)s,
									  %(load_duration)s, %(install_duration)s, %(check_duration)s, %(load_log)s, %(install_log)s, %(check_log)s, %(diff)s)''',
							  {'uuid' : args.uuid, 'machine' : machine['id'], 'version' : version['id'], 'pgversion' : get_pg_version(args.config),
							   'load' : (args.load != 'unknown' and args.load or None), 'install' : (args.install != 'unknown' and args.install or None), 'check' : (args.check != 'unknown' and args.check or None),
							   'install_log' : base64.b64decode(args.install_log), 'load_log' : base64.b64decode(args.load_log), 'check_log' : base64.b64decode(args.check_log), 'diff' : base64.b64decode(args.check_diff),
							   'install_duration' : args.install_duration, 'load_duration' : args.load_duration, 'check_duration' : args.check_duration, 
							   'config' : args.config, 'env' : args.env})

			conn.commit()

		return {'uuid' : args.uuid}


class Result(Resource):
	'info about a particular test (identified by UUID)'

	# basic version info
	info_sql = """SELECT result_uuid AS uuid, m.name AS machine, user_name AS user, dist_name AS dist, version_number AS version, isodate(version_date) AS date, version_status AS state,
						 isodate(submit_date) AS test_date, pg_version, pg_config, env_info, load_result, install_result, check_result,
						 load_duration, install_duration, check_duration, log_load, log_install, log_check, check_diff
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)
										 JOIN results r ON (r.dist_version_id = v.id)
										 JOIN machines m ON (m.id = r.machine_id)
					WHERE result_uuid = %(uuid)s"""

	def get(self, rid):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Result.info_sql, {'uuid' : rid})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown result UUID")

		return (info)