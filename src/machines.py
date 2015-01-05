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

	# list of distributions / versions already tested by this machine (only the last result)
	results_sql = """SELECT dist_name AS name, version_number AS version, r.pg_version, rl.pg_version AS pg_version_major
							FROM results_last rl JOIN distribution_versions v ON (rl.dist_version_id = v.id)
												 JOIN distributions d ON (v.dist_id = d.id)
												 JOIN results r ON (r.id = rl.result_id)
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

		tested = {}
		for r in results:

			if r['name'] not in tested:
				tested.update({r['name'] : {}})

			if r['version'] not in tested[r['name']]:
				tested[r['name']].update({r['version'] : {'major' : [], 'minor' : []}})

			tested[r['name']][r['version']]['minor'].append(r['pg_version'])
			tested[r['name']][r['version']]['major'].append(r['pg_version_major'])


		for name in tested:
			for version in tested[name]:
				tested[name][version]['minor'] = list(set(tested[name][version]['minor']))
				tested[name][version]['major'] = list(set(tested[name][version]['major']))


		return ({'info' : info, 'tested' : tested, 'stats' : stats})

class MachineQueue(Resource):

	# list extensions not processed by a machine with a particular name
	queue_sql = """SELECT
						d.dist_name AS name,
						dv.version_number AS version,
						dv.version_meta AS meta
					FROM distribution_versions dv JOIN distributions d ON (d.id = dv.dist_id)
					WHERE dv.id NOT IN (
						SELECT dist_version_id
							FROM results r JOIN machines m ON (m.id = r.machine_id)
							WHERE m.name = %(name)s AND pg_version = %(pgversion)s)
					ORDER BY dist_name, version_number"""

	def _check_prerequisities(self, pgversion, prereqs):
		'verifies requirements on PostgreSQL version'

		for prereq in prereqs:
			tmp = [v.strip() for v in prereq.split(',')]
			for r in tmp:
				res = re.match('(>|>=|=|==|<=|<)?(\s+)?([0-9]+\.[0-9]+\.[0-9]+)', r)
				if res:
					operator = res.group(1)
					version = SemVer(res.group(3))

					if (operator is None) or (operator == '>='):
						if not (pgversion >= version):
							return False
					elif (operator == '=') or (operator == '=='):
						if not (pgversion == version):
							return False
					elif (operator == '>'):
						if not (pgversion > version):
							return False
					elif (operator == '>='):
						if not (pgversion >= version):
							return False
					elif (operator == '<'):
						if not (pgversion < version):
							return False
					elif (operator == '<='):
						if not (pgversion <= version):
							return False
					else:
						print "unknown operator in prerequisity:",r

				else:
					print "skipping invalid prerequisity :",r

		return True

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

	def get(self, name, pgversion):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(MachineQueue.queue_sql, {'name' : name, 'pgversion' : pgversion})
			qlist = cursor.fetchall()

		# the SQL only filters out distributions already tested on that exact version - we still
		# have to check the prerequisities and remove those incompatible with the pg version
		results = []
		for q in qlist:
			prereqs = self._extract_prereqs(q['meta'])
			if self._check_prerequisities(pgversion, prereqs):
				results.append({'name': q['name'], 'version' : q['version']})

		return (results)
