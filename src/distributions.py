import flask
from flask.ext.restful import Resource, abort, reqparse
from flask import request

def result_parser():

	result_parser = reqparse.RequestParser()
	result_parser.add_argument('machine', type=str, required=True, location='json')
	result_parser.add_argument('signature', type=str, required=True, location='json')
	result_parser.add_argument('load', type=str, location='json')
	result_parser.add_argument('install', type=str, location='json')
	result_parser.add_argument('check', type=str, location='json')
	result_parser.add_argument('install_log', type=str, location='json')
	result_parser.add_argument('load_log', type=str, location='json')
	result_parser.add_argument('check_log', type=str, location='json')
	result_parser.add_argument('check_diff', type=str, location='json')

	return result_parser

from db import DB
from utils import verify_signature
import uuid

class DistributionList(Resource):
	'list of known distributions (some may not be tested yet)'

	def get(self):
		'list distributions, along with info about author (optional filtering)'

		where = []
		params = {}

		# filter only distributions published by the particular user
		if 'user' in request.args:
			where.append('user_name = %(user)s')
			params.update({'user' : request.args['user']})

		if where:
			sql = """SELECT user_name AS user, dist_name AS name,
							install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM distributions d JOIN users u ON (d.user_id = u.id)
											 LEFT JOIN results_distribution rd ON (rd.dist_id = d.id)
						WHERE %(cond)s
						ORDER BY dist_name""" % {'cond' : " AND ".join(where)}
		else:
			sql = """SELECT user_name AS user, dist_name AS name,
							install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM distributions d JOIN users u ON (d.user_id = u.id)
											 LEFT JOIN results_distribution rd ON (rd.dist_id = d.id)
						ORDER BY dist_name"""

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(sql, params)
			tmp = cursor.fetchall()

		distributions = []
		for r in tmp:
			distributions.append({'user' : r['user'], 'name' : r['name'],
						 'install' : {'ok' : r['install_ok'], 'error' : r['install_error']},
						 'load' : {'ok' : r['load_ok'], 'error' : r['load_error']},
						 'check' : {'ok' : r['check_ok'], 'error' : r['check_error'], 'missing' : r['check_missing']}})

		return distributions

class Distribution(Resource):

	# basic distribution info
	info_sql = """SELECT user_name AS user, dist_name AS name
					FROM distributions d JOIN users u ON (d.user_id = u.id)
					WHERE dist_name = %(name)s"""

	# list of versions for the distribution
	versions_sql = """SELECT version_number AS version, isodate(version_date) AS date, version_status AS status, version_meta AS meta,
							 install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
											 LEFT JOIN results_version rv ON (v.id = rv.dist_version_id)
						WHERE dist_name = %(name)s ORDER BY version_date DESC"""

	# summary of distribution results (last result for each status)
	summary_sql = """SELECT version_status,
							install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM distributions d JOIN users u ON (d.user_id = u.id)
											 LEFT JOIN results_distribution_status rd ON (rd.dist_id = d.id)
						WHERE dist_name = %(name)s"""

	def _extract_prereqs(self, meta):

		'''extract prerequisities (required PostgreSQL versions)'''
		prereqs = []

		if (meta is None) or ('prereqs' not in meta):
			return []

		for prereq_type in ['configure', 'build', 'test', 'runtime']:
			if prereq_type in meta['prereqs']:
				if 'requires' in meta['prereqs'][prereq_type]:
					for v in meta['prereqs'][prereq_type]['requires']:
						prereqs.append({v : meta['prereqs'][prereq_type]['requires'][v]})

		# extract only PostgreSQL-related prerequisities
		return [v['PostgreSQL'] for v in prereqs if ('PostgreSQL' in v)]

	def get(self, name):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Distribution.info_sql, {'name' : name})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown distribution")

		with DB() as (conn, cursor):

			# list of versions
			cursor.execute(Distribution.versions_sql, {'name' : name})
			tmp = cursor.fetchall()

			# no version of the distribution exists -> 404
			if not tmp:
				abort(404, message="no versions for the distribution")

		# extract the prerequisities from the meta (but only those related to PostgreSQL)
		versions = []
		for v in tmp:
			versions.append({
					'version' : v['version'],
					'prereqs' : self._extract_prereqs(v['meta']),
					'date' : v['date'],
					'status' : v['status'],
					'install' : {'ok' : v['install_ok'], 'error' : v['install_error']},
					'load' : {'ok' : v['load_ok'], 'error' : v['load_error']},
					'check' : {'ok' : v['check_ok'], 'error' : v['check_error'], 'missing' : v['check_missing']}
				})

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Distribution.summary_sql, {'name' : name})
			tmp = cursor.fetchall()

		summary = {}
		for r in tmp:
			summary.update({r['version_status'] : {
									'install' : {'ok' : r['install_ok'], 'error' : r['install_error']},
									'load' : {'ok' : r['load_ok'], 'error' : r['load_error']},
									'check' : {'ok' : r['check_ok'], 'error' : r['check_error'], 'missing' : r['check_missing']}}})

		# add info about versions
		info.update({'versions' : versions})

		# add summary of test results
		info.update({'summary' : summary})

		return (info)


class Version(Resource):
	'info about a distribution version'

	# basic version info
	info_sql = """SELECT user_name AS user, dist_name AS name, version_number AS version, isodate(version_date) AS date, version_status AS status, version_meta AS meta
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)
					WHERE dist_name = %(name)s AND version_number = %(version)s"""

	stats_sql = """SELECT r.result_uuid, m.name AS machine, vd.pg_version, isodate(submit_date) AS date, install, load, "check"
					FROM results_version_details vd JOIN results r ON (r.id = vd.result_id)
													JOIN distribution_versions dv ON (r.dist_version_id = dv.id)
													JOIN distributions d ON (dv.dist_id = d.id)
													JOIN machines m ON (r.machine_id = m.id)
					WHERE dist_name = %(name)s AND version_number = %(version)s
					ORDER BY m.name, pg_version DESC"""

	summary_sql = """SELECT install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM results_version rv JOIN distribution_versions dv ON (rv.dist_version_id = dv.id)
												JOIN distributions d ON (dv.dist_id = d.id)
					WHERE dist_name = %(name)s AND version_number = %(version)s"""

	def get(self, name, version):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Version.info_sql, {'name' : name, 'version' : version})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown distribution/version")

			# info about distribution
			cursor.execute(Version.stats_sql, {'name' : name, 'version' : version})
			tmp = cursor.fetchall()

			stats = {t['machine'] : [] for t in tmp}
			for r in tmp:
				stats[r['machine']].append({
							'version' : r['pg_version'],
							'date' : r['date'],
							'install' : r['install'] or '',
							'load' : r['load'] or '',
							'check' : r['check'] or '',
							'uuid' : r['result_uuid']
						})

			# fetch only some fields of the META
			for key in ['date', 'abstract', 'description']:
				if key in info:
					info[key] = info['meta'][key]
				else:
					info[key] = ''

			del info['meta']

			info['stats'] = stats

			# get summary of the results
			cursor.execute(Version.summary_sql, {'name' : name, 'version' : version})
			tmp = cursor.fetchone()

			if tmp:
				info['summary'] = {'install' : {'ok' : tmp['install_ok'], 'error' : tmp['install_error']},
								   'load' : {'ok' : tmp['load_ok'], 'error' : tmp['load_error']},
								   'check' : {'ok' : tmp['check_ok'], 'error' : tmp['check_error'], 'missing' : tmp['check_missing']}}

		return (info)
