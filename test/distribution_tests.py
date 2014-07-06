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

class TestEmpty(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE users CASCADE")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/distributions')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [])

		# unknown distribution
		response = self.app.get('/api/diststributions/xxx')
		self.assertEqual(response.status_code, 404)

		response = self.app.get('/api/distributions/xxx/1.2.3')
		self.assertEqual(response.status_code, 404)

	def test_post_requests(self):

		# only GET is allowed on these URIs
		response = self.app.post('/api/distributions')
		self.assertEqual(response.status_code, 405)

		response = self.app.post('/api/distributions/xxx')
		self.assertEqual(response.status_code, 405)

		response = self.app.post('/api/distributions/xxx/1.2.3')
		self.assertEqual(response.status_code, 405)


class TestSingle(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE users CASCADE")

			# create a single user/distribution/version
			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/distributions')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'user' : 'test_user', 'dist' : 'testdistr'}])

		# existing distribution
		response = self.app.get('/api/distributions/testdistr')
		self.assertEqual(response.status_code, 200)

		# unknown distribution
		response = self.app.get('/api/distributions/testdistr2')
		self.assertEqual(response.status_code, 404)

		# known distribution / known version
		response = self.app.get('/api/distributions/testdistr/1.2.3')
		self.assertEqual(response.status_code, 200)

		# known distribution / unknown version
		response = self.app.get('/api/distributions/testdistr/1.2.4')
		self.assertEqual(response.status_code, 404)

		# unknown distribution / known version
		response = self.app.get('/api/distributions/testdistr2/1.2.3')
		self.assertEqual(response.status_code, 404)

		# unknown distribution / unknown version
		response = self.app.get('/api/distributions/testdistr2/1.2.4')
		self.assertEqual(response.status_code, 404)


class TestMultiple(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE users CASCADE")

			# create a single user/distribution/version
			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")

			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user2', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr2')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 03:04:05', 'stable')")

			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user3', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr3')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.5', '2014-01-02 03:04:05', 'stable')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/distributions')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'user' : 'test_user', 'dist' : 'testdistr'}, {'user' : 'test_user2', 'dist' : 'testdistr2'}, {'user' : 'test_user3', 'dist' : 'testdistr3'}])

		# existing distribution
		response = self.app.get('/api/distributions/testdistr')
		self.assertEqual(response.status_code, 200)

		# second existing distribution
		response = self.app.get('/api/distributions/testdistr2')
		self.assertEqual(response.status_code, 200)

		# known distribution / matching version
		response = self.app.get('/api/distributions/testdistr2/1.2.4')
		self.assertEqual(response.status_code, 200)

		# known distribution / mismatching version
		response = self.app.get('/api/distributions/testdistr3/1.2.4')
		self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
	unittest.main()