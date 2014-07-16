import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB
from utils import verify_signature
import uuid

class MachineList(Resource):
	'list of known distributions (some may not be tested yet)'

	# list of machines with info about tested distributions, versions
	# TODO add number of failures (total and for last versions)
	list_sql = """SELECT m.name AS name, is_active, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions, COALESCE(tests, 0) AS tests, last_test_date,
							install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
					FROM machines m LEFT JOIN (
						SELECT
							machine_id,
							COUNT(DISTINCT dist_id) AS distributions, COUNT(DISTINCT dist_version_id) AS versions, COUNT(*) AS tests,
							isodate(MAX(submit_date)) AS last_test_date
						FROM results r JOIN distribution_versions v ON (r.dist_version_id = v.id) JOIN distributions d ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (m.id = s.machine_id)
					LEFT JOIN (
						SELECT
							machine_id,
							SUM(install_ok)::int AS install_ok, SUM(install_error)::int AS install_error, 
							SUM(load_ok)::int AS load_ok, SUM(load_error)::int AS load_error, 
							SUM(check_ok)::int AS check_ok, SUM(check_error)::int AS check_error, SUM(check_missing)::int AS check_missing
						FROM results_machine GROUP BY 1
					) AS stats ON (m.id = stats.machine_id)
					ORDER BY m.name"""

	def get(self, user=None, release=None, status=None, last=None, machine=None):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(MachineList.list_sql)
			tmp = cursor.fetchall()

		machines = []
		for r in tmp:
			machines.append({
					'name' : r['name'],
					'is_active' : r['is_active'],
					'distributions' : r['distributions'],
					'versions' : r['versions'],
					'tests' : r['tests'],
					'last_test_date' : r['last_test_date'],
					'install' : {'ok' : r['install_ok'], 'error' : r['install_error']},
					'load' : {'ok' : r['load_ok'], 'error' : r['load_error']},
					'check' : {'ok' : r['check_ok'], 'error' : r['check_error'], 'missing' : r['check_missing']}
				})

		return machines

	def post(self):

		# FIXME implement some sort of rate limits, i.e. no IP can submit over 60 machines per hour or something like that
		# FIXME implement submission of a new test machine

		return {'result' : 'OK'}

class Machine(Resource):

	# basic user info
	# TODO add info about extensions with failing / passing last version
	info_sql = """SELECT m.name AS name, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions, COALESCE(tests, 0) AS tests, is_active, m.description, last_test_date
					FROM machines m LEFT JOIN (
						SELECT
							machine_id,
							COUNT(DISTINCT dist_id) AS distributions, COUNT(DISTINCT dist_version_id) AS versions, COUNT(*) AS tests,
							isodate(MAX(submit_date)) AS last_test_date
						FROM results r JOIN distribution_versions v ON (r.dist_version_id = v.id) JOIN distributions d ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (m.id = s.machine_id) WHERE m.name = %(name)s"""

	# list of distribution versions for the user, along with number
	# TODO add number of failures (total and for last versions)
	results_sql = """SELECT dist_name AS name, version_number AS version, isodate(version_date) AS date, version_status AS status
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
											 JOIN results r ON (r.dist_version_id = v.id)
											 JOIN machines m ON (r.machine_id = m.id)
						WHERE m.name = %(name)s"""

	stats_sql = """SELECT
						pg_version,
						status,
						install_ok, install_error, load_ok, load_error, check_ok, check_error, check_missing
					FROM results_machine rm JOIN machines m ON (m.id = rm.machine_id) WHERE m.name = %(name)s"""

	def get(self, name):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Machine.info_sql, {'name' : name})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown user")

			# list of versions
			cursor.execute(Machine.results_sql, {'name' : name})
			results = cursor.fetchall()

			# list of versions
			cursor.execute(Machine.stats_sql, {'name' : name})
			tmp = cursor.fetchall()

		stats = {v['pg_version'] : {} for v in tmp}

		for r in tmp:
			stats[r['pg_version']].update({r['status'] : {
					'install' : {'ok' : r['install_ok'], 'error' : r['install_error']},
					'load' : {'ok' : r['load_ok'], 'error' : r['load_error']},
					'check' : {'ok' : r['check_ok'], 'error' : r['check_error'], 'missing' : r['check_missing']},
				}})

		return ({'info' : info, 'results' : results, 'stats' : stats})
