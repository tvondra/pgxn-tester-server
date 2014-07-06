import json
import sys
import os.path
import unittest

# the libraries are located in the '../src', so add it to the python path
sys.path.append(os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0], 'src'))

from main import app
from db import DB

from utils import sign_request

# test configuration
import config

class TestResultPost(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE users CASCADE")
			cursor.execute("TRUNCATE animals CASCADE")

			# create a single user/distribution/version
			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO animals (animal_name, animal_secret, animal_desc, animal_email) VALUES ('testanimal', 'testsecret', 'animal description', 'animal@example.com')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_invalid_distribution(self):

		result = {  "animal" : "testanimal",
					"distribution" : "testdist",
					"version" : "1.2.3",
					"load" : "success",
					"install" : "success",
					"check" : "failure",
					"install_log" : "pgxnclient install logfile",
					"load_log" : "pgxnclient load logfile",
					"check_log" : "pgxnclient check logfile",
					"check_diff" : "pg_regress diff file" }


		result['signature'] = sign_request(data=result, secret='testsecret')

		# list distributions (there are none)
		response = self.app.post('/api/results', data=json.dumps(result), content_type='application/json')

		self.assertEqual(response.status_code, 401)
		self.assertEqual(json.loads(response.data), {'message' : 'unknown distribution'})

	def test_invalid_version(self):

		result = {  "animal" : "testanimal",
					"distribution" : "testdistr",
					"version" : "1.0.0",
					"load" : "success",
					"install" : "success",
					"check" : "failure",
					"install_log" : "pgxnclient install logfile",
					"load_log" : "pgxnclient load logfile",
					"check_log" : "pgxnclient check logfile",
					"check_diff" : "pg_regress diff file" }


		result['signature'] = sign_request(data=result, secret='testsecret')

		# list distributions (there are none)
		response = self.app.post('/api/results', data=json.dumps(result), content_type='application/json')

		self.assertEqual(response.status_code, 401)
		self.assertEqual(json.loads(response.data), {'message' : 'unknown version'})

	def test_correct_signature(self):

		result = {  "animal" : "testanimal",
					"distribution" : "testdistr",
					"version" : "1.2.3",
					"load" : "success",
					"install" : "success",
					"check" : "failure",
					"install_log" : "pgxnclient install logfile",
					"load_log" : "pgxnclient load logfile",
					"check_log" : "pgxnclient check logfile",
					"check_diff" : "pg_regress diff file" }


		result['signature'] = sign_request(data=result, secret='testsecret')

		# list distributions (there are none)
		response = self.app.post('/api/results', data=json.dumps(result), content_type='application/json')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(json.loads(response.data)['uuid']), 36)

	def test_incorrect_signature(self):

		result = {  "animal" : "testanimal",
					"distribution" : "testdist",
					"version" : "1.0.0",
					"load" : "success",
					"install" : "success",
					"check" : "failure",
					"install_log" : "pgxnclient install logfile",
					"load_log" : "pgxnclient load logfile",
					"check_log" : "pgxnclient check logfile",
					"check_diff" : "pg_regress diff file" }


		result['signature'] = sign_request(data=result, secret='incorrect')

		# list distributions (there are none)
		response = self.app.post('/api/results', data=json.dumps(result), content_type='application/json')

		# 401 - unauthorized
		self.assertEqual(response.status_code, 401)
		self.assertEqual(json.loads(response.data), {'message' : 'invalid signature'})

if __name__ == '__main__':
	unittest.main()