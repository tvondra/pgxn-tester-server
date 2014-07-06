import flask
from flask.ext.restful import Resource, abort, reqparse

def result_parser():

	result_parser = reqparse.RequestParser()
	result_parser.add_argument('animal', type=str, required=True, location='json')
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

	def get(self, user=None, release=None, status=None, last=None, animal=None):
		'list distributions, along with info about author (optional filtering)'

		sql = """SELECT user_name AS user, dist_name AS dist
					FROM distributions d JOIN users u ON (d.user_id = u.id)
					ORDER BY dist_name"""

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(sql)
			dists = cursor.fetchall()

		return dists

class Distribution(Resource):

	# basic distribution info
	info_sql = """SELECT user_name AS user, dist_name AS dist
					FROM distributions d JOIN users u ON (d.user_id = u.id)
					WHERE dist_name = %(name)s"""

	# list of versions for the distribution
	versions_sql = """SELECT dist_version AS version, isodate(dist_date) AS date, dist_status AS status
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
						WHERE dist_name = %(name)s"""

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
			versions = cursor.fetchall()

			# no version of the distribution exists -> 404
			if not versions:
				abort(404, message="no versions for the distribution")

		# add info about versions
		info.update({'versions' : versions})

		# add summary of test results
		info.update({'summary' : {}})

		return (info)


class Version(Resource):
	'info about a distribution version'

	# basic version info
	info_sql = """SELECT user_name AS user, dist_name AS dist, dist_version AS version, isodate(dist_date) AS date, dist_status AS state
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)
					WHERE dist_name = %(name)s AND dist_version = %(version)s"""

	def get(self, name, version):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Version.info_sql, {'name' : name, 'version' : version})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown distribution")

		return ({'info' : info, 'summary' : {}})
