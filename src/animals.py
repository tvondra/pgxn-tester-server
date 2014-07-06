import flask
from flask.ext.restful import Resource, abort, reqparse

from db import DB
from utils import verify_signature
import uuid

class AnimalList(Resource):
	'list of known distributions (some may not be tested yet)'

	# list of animals with info about tested distributions, versions
	# TODO add number of failures (total and for last versions)
	list_sql = """SELECT animal_name AS name, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions, COALESCE(tests, 0) AS tests
					FROM animals a LEFT JOIN (
						SELECT animal_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(DISTINCT dist_version_id) AS versions, COUNT(*) AS tests
						FROM results r JOIN distribution_versions v ON (r.dist_version_id = v.id) JOIN distributions d ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (a.id = s.animal_id) ORDER BY animal_name"""

	def get(self, user=None, release=None, status=None, last=None, animal=None):
		'list distributions, along with info about author (optional filtering)'

		with DB() as (conn, cursor):

			# list distributions, along with info about author
			cursor.execute(AnimalList.list_sql)
			animals = cursor.fetchall()

		return animals

	def post(self):

		# FIXME implement some sort of rate limits, i.e. no IP can submit over 60 animals per hour or something like that

		return {'result' : 'OK'}

class Animal(Resource):

	# basic user info
	# TODO add info about extensions with failing / passing last version
	info_sql = """SELECT animal_name AS name, COALESCE(distributions, 0) AS distributions, COALESCE(versions, 0) AS versions, COALESCE(tests, 0) AS tests
					FROM animals a LEFT JOIN (
						SELECT animal_id, COUNT(DISTINCT dist_id) AS distributions, COUNT(DISTINCT dist_version_id) AS versions, COUNT(*) AS tests
						FROM results r JOIN distribution_versions v ON (r.dist_version_id = v.id) JOIN distributions d ON (v.dist_id = d.id) GROUP BY 1
					) AS s ON (a.id = s.animal_id) WHERE animal_name = %(name)s"""

	# list of distribution versions for the user, along with number
	# TODO add number of failures (total and for last versions)
	results_sql = """SELECT dist_name AS name, dist_version AS version, isodate(dist_date) AS date, dist_status AS status
						FROM distributions d JOIN distribution_versions v ON (d.id = v.dist_id)
											 JOIN results r ON (r.dist_version_id = v.id)
											 JOIN animals a ON (r.animal_id = a.id)
						WHERE animal_name = %(name)s"""

	def get(self, name):
		'get info about distribution, along with info about author'

		with DB() as (conn, cursor):

			# info about distribution
			cursor.execute(Animal.info_sql, {'name' : name})
			info = cursor.fetchone()

			# distribution does not exist -> 404
			if not info:
				abort(404, message="unknown user")

		with DB() as (conn, cursor):

			# list of versions
			cursor.execute(Animal.results_sql, {'name' : name})
			results = cursor.fetchall()

		return ({'info' : info, 'results' : results})
