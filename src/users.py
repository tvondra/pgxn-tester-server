import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB
from utils import verify_signature
import uuid

class UserList(Resource):
	'list of known distributions (some may not be tested yet)'

	# list of users with info about published distributions, versions
	# TODO add number of failures (total and for last versions)
	list_sql = """SELECT user_name AS user, full_name, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions,
							install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
					FROM users u LEFT JOIN (
						SELECT user_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(*) AS versions
						FROM distributions d JOIN distribution_versions v ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (s.user_id = u.id)
					LEFT JOIN (
						SELECT user_id,
								SUM(install_ok)::int AS install_ok, SUM(install_error)::int AS install_error,
								SUM(load_ok)::int AS load_ok, SUM(load_error)::int AS load_error,
								SUM(check_ok)::int AS check_ok, SUM(check_error)::int AS check_error, SUM(check_missing)::int AS check_missing
						FROM results_version rv
							JOIN version_last vl ON (rv.dist_version_id = vl.version_id)
							JOIN distribution_versions dv ON (vl.version_id = dv.id)
							JOIN distributions d ON (d.id = dv.dist_id)
						GROUP BY user_id
					) AS stats ON (stats.user_id = u.id)
					ORDER BY user_name"""

	def get(self, user=None, release=None, status=None, last=None, machine=None):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(UserList.list_sql)
			tmp = cursor.fetchall()

		users = []
		for r in tmp:
			users.append({'name' : r['user'], 'full_name' : r['full_name'], 'distributions' : r['distributions'], 'versions' : r['versions'],
						 'install' : {'ok' : r['install_ok'], 'error' : r['install_error']},
						 'load' : {'ok' : r['load_ok'], 'error' : r['load_error']},
						 'check' : {'ok' : r['check_ok'], 'error' : r['check_error'], 'missing' : r['check_missing']}})

		return users

class User(Resource):

	# basic user info
	# TODO add info about extensions with failing / passing last version
	info_sql = """SELECT user_name AS user, full_name AS name, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions
					FROM users u LEFT JOIN (
						SELECT user_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(*) AS versions
						FROM distributions d JOIN distribution_versions v ON (v.dist_id = d.id)
						GROUP BY 1
					) AS s ON (u.id = s.user_id) WHERE user_name = %(name)s"""

	# list of versions published by the user user
	# TODO add number of successes / failures for each version
	versions_sql = """SELECT dist_name AS name, version_number AS version, isodate(version_date) AS date, version_status AS status,
							 install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
											 JOIN users u ON (d.user_id = u.id)
											 LEFT JOIN results_version rv ON (v.id = rv.dist_version_id)
						WHERE user_name = %(name)s ORDER BY dist_name, version_number DESC"""

	def get(self, name):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(User.info_sql, {'name' : name})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown user")

		with DB() as (conn, cursor):

			# list of versions
			cursor.execute(User.versions_sql, {'name' : name})
			tmp = cursor.fetchall()

		# distribution => version => {date, status, install : {}, load : {}, check : {}}
		distributions = {v['name'] : [] for v in tmp}

		for row in tmp:
			distributions[row['name']].append({
					'version' : row['version'],
					'date' : row['date'],
					'status' : row['status'],
					'install' : {'ok' : row['install_ok'], 'error' : row['install_error']},
					'load' : {'ok' : row['load_ok'], 'error' : row['load_error']},
					'check' : {'ok' : row['check_ok'], 'error' : row['check_error'], 'missing' : row['check_missing']}
				});

		return ({'info' : info, 'distributions' : distributions})
