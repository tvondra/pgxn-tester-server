import flask
from flask.ext.restful import Resource, abort, reqparse

def result_parser():

	result_parser = reqparse.RequestParser()
	result_parser.add_argument('distribution', type=str, required=True, location='json')
	result_parser.add_argument('version', type=str, required=True, location='json')
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

class ResultList(Resource):

	# basic list of results with basic info (no detailed logs)
	list_sql = """SELECT dist_version AS version, isodate(dist_date) AS date, dist_status AS state
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)"""

	def get(self):
		'get info about distribution, along with info about author'

		# TODO add some basic paging of results (using submit_date of the results)

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(ResultList.list_sql)
			results = cursor.fetchall()

		return results

	def post(self):

		# FIXME implement some sort of size limits, i.e. no results over 1MB or something like that
		# FIXME implement some sort of rate limits, i.e. no client can submit over 1000 results per hour or something like that

		args = result_parser().parse_args()
		data = dict((k,args[k]) for k in args if k != 'signature') 

		if not verify_signature(data, secret='testsecret', signature=args.signature):
			abort(401, message='invalid signature')

		# FIXME implement proper validation of the data (check existence of distribution/version etc.)

		if args.distribution != 'testdistr':
			# FIXME proper distribution check
			abort(401, message='unknown distribution')

		elif args.version != '1.2.3':
			# FIXME proper version check
			abort(401, message='unknown version')

		return {'uuid' : str(uuid.uuid4())}


class Result(Resource):
	'info about a particular test (identified by UUID)'

	# basic version info
	info_sql = """SELECT user_name AS user, dist_name AS dist, dist_version AS version, isodate(dist_date) AS date, dist_status AS state
					FROM distributions d JOIN users u ON (d.user_id = u.id)
										 JOIN distribution_versions v ON (d.id = v.dist_id)
					WHERE result_uuid = %(uuid)s"""

	def get(self, rid):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Version.info_sql, {'uuid' : rid})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown result UUID")

		return ({'info' : info, 'summary' : {}})