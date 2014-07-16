import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB

class Stats(Resource):
	'list of known distributions (some may not be tested yet)'

	# TODO This is a good candidate for materialized view

	# basic distribution statistics
	basic_sql = """SELECT COUNT(DISTINCT dist_id) AS distributions, COUNT(DISTINCT v.id) AS versions, COUNT(*) AS tests FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)"""

	# stats of install/load/check phases (per PostgreSQL major version and distribution status)
	summary_sql = """SELECT * FROM results_summary"""

	def get(self, user=None, release=None, status=None, last=None, machine=None):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# basic simple statistics
			cursor.execute(Stats.basic_sql)
			basic = cursor.fetchone()

			cursor.execute(Stats.summary_sql)
			summary = cursor.fetchall()

		# get versions in the result
		versions = sorted(set([row['pg_version'] for row in summary]))

		# aggregate the results into a simple hierarchical JSON
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

		return {'basic' : basic, 'versions' : versions, 'results' : results}
