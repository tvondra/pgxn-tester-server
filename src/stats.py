import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB

class Overview(Resource):
	'''Simple summary statistics
	(a) number of distributions, distribution versions and executed tests
	(b) result stats per PostgreSQL major version and distribution status
	'''

	# basic distribution statistics
	_basic_sql = """SELECT
						COUNT(DISTINCT dist_id) AS distributions,
						COUNT(DISTINCT v.id) AS versions,
						COUNT(*) AS tests
					FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)"""

	# stats of install/load/check phases (per PostgreSQL major version and distribution status)
	_summary_sql = """SELECT * FROM results_summary"""

	def get(self):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# basic summary stats
			cursor.execute(Overview._basic_sql)
			basic = cursor.fetchone()

			# stats per major version
			cursor.execute(Overview._summary_sql)
			summary = cursor.fetchall()

		# get PostgreSQL (major) versions in the result
		pg_versions = sorted(set([row['pg_version'] for row in summary]))

		# transform into a hierarchical JSON (major_version => status => stats)
		results = {}

		for row in summary:

			if row['pg_version'] not in results:
				results.update({row['pg_version'] : {}})

			results[row['pg_version']].update({
								row['status'] : {
										'install' : {'ok' : row['install_ok'], 'error' : row['install_error']},
										'load' : {'ok' : row['load_ok'], 'error' : row['load_error']},
										'check' : {'ok' : row['check_ok'], 'error' : row['check_error'], 'missing' : row['check_missing']}
									}})

		return {'basic' : basic, 'versions' : pg_versions, 'results' : results}


class CurrentTotals(Resource):
	'''current summary stats, i.e. number of tests (single row), computed from

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.
	'''

	_sql = """SELECT
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_current"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(CurrentTotals._sql)
			stats = cursor.fetchone()

		return stats


class CurrentVersions(Resource):
	'''current stats, i.e. number of tests, per major version, computed using:

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.

	This is essentially the same as CurrentTotals, but broken down by
	PostgreSQL major version.
	'''

	_sql = """SELECT
					major_version,
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_current_versions
				ORDER BY major_version"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(CurrentVersions._sql)
			stats = cursor.fetchall()

		return stats

class CurrentStatus(Resource):
	'''current stats, i.e. number of tests, per release status, computed using:

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.

	This is essentially the same as CurrentVersions, but broken down by
	release status. The results are returned as a dict {status => data}.
	'''

	_sql = """SELECT
					version_status,
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_current_version_status
				ORDER BY version_status"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(CurrentStatus._sql)
			stats = cursor.fetchall()

		result = {}

		# transform the results into {status => data}
		for s in stats:
			status = s['version_status']
			del s['version_status']
			result.update({status : s})

		return result


class MonthlyTotals(Resource):
	'''monthly summary, i.e. number of tests (single row), computed from

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.

	This is essentially the same as CurrentTotals, but broken down by
	month of the distribution release.
	'''

	_sql = """SELECT
					isodate(release_month) as month,
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_monthly
				ORDER BY release_month"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(MonthlyTotals._sql)
			stats = cursor.fetchall()

		return stats


class MonthlyVersions(Resource):
	'''current stats, i.e. number of tests, per major version, computed using:

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.

	This is essentially the same as CurrentVersions, but broken down by
	month of the distribution release.
	'''

	_sql = """SELECT
					isodate(release_month) as release_month,
					major_version,
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_monthly_versions
				ORDER BY release_month, major_version"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(MonthlyVersions._sql)
			stats = cursor.fetchall()

		return stats


class MonthlyStatus(Resource):
	'''current stats, i.e. number of tests, per release status, computed using:

	(a) last version per distribution status
	(b) last result from each machine and major version

	So a distribution with multiple releases marked as 'stable', only
	the most recent one will be considered. If the distribution has
	several releases marked as 'stable' and several releases marked as
	'testing' then the last version for each status will be considered.

	This is essentially the same as MonthlyVersions, but broken down by
	release status. The results are returned as a dict {status => data}.
	'''

	_sql = """SELECT
					isodate(release_month) as release_month,
					version_status,
					total_count,
					version_count,
					install_errors,
					load_errors,
					check_errors,
					check_missing,
					ok_count
				FROM stats_monthly_version_status
				ORDER BY release_month, version_status"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(MonthlyStatus._sql)
			stats = cursor.fetchall()

		results = []
		month = {}
		current_month = None

		# transform the results into list of disctionaries, mapping status to data
		# {stable => data, unstable => data, testing => data}
		for s in stats:

			if s['release_month'] != current_month and current_month is not None:
				results.append(month)
				month = {}

			status = s['version_status']
			current_month = s['release_month']

			del s['release_month']
			del s['version_status']

			month.update({'month' : current_month})
			month.update({status : s})

		results.append(month)

		return results


class ErrorsOverview(Resource):
	'''summary of causes of failures (all releases, last test for each)'''

	_sql = """SELECT
					error_phase,
					description,
					count
				FROM stats_errors
				ORDER BY count DESC"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(ErrorsOverview._sql)
			stats = cursor.fetchall()

		return stats


class ErrorsPerStatus(Resource):
	'''summary of causes of failures, per release status'''

	_sql = """SELECT
					error_phase,
					version_status,
					description,
					count
				FROM stats_errors_status
				ORDER BY count DESC"""

	def get(self):

		with DB() as (conn, cursor):

			cursor.execute(ErrorsPerStatus._sql)
			stats = cursor.fetchall()

		result = {}

		for s in stats:
			status = s['version_status']
			del s['version_status']

			if status not in result:
				result.update({status : []})

			result[status].append(s)

		return result
