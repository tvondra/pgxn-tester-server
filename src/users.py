import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB
from utils import verify_signature
import uuid

class UserList(Resource):
	'list of known distributions (some may not be tested yet)'

	# list of users with info about published distributions, versions
	# TODO add number of failures (total and for last versions)
	list_sql = """SELECT user_name AS user, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions
					FROM users u LEFT JOIN (
						SELECT user_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(*) AS versions
						FROM distributions d JOIN distribution_versions v ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (s.user_id = u.id) ORDER BY user_name"""

	def get(self, user=None, release=None, status=None, last=None, animal=None):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(UserList.list_sql)
			users = cursor.fetchall()

		return users

class User(Resource):

	# basic user info
	# TODO add info about extensions with failing / passing last version
	info_sql = """SELECT user_name AS user, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions
					FROM users u LEFT JOIN (
						SELECT user_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(*) AS versions
						FROM distributions d JOIN distribution_versions v ON (v.dist_id = d.id)
						GROUP BY 1
					) AS s ON (u.id = s.user_id) WHERE user_name = %(name)s"""

	# list of distribution versions for the user, along with number
	# TODO add number of failures (total and for last versions)
	results_sql = """SELECT dist_name AS name, dist_version AS version, isodate(dist_date) AS date, dist_status AS status
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
											 JOIN users u ON (d.user_id = u.id)
						WHERE user_name = %(name)s"""

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
			cursor.execute(User.results_sql, {'name' : name})
			results = cursor.fetchall()

		return ({'info' : info, 'results' : results})
