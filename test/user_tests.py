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
		response = self.app.get('/api/users')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [])

		# unknown distribution
		response = self.app.get('/api/users/xxx')
		self.assertEqual(response.status_code, 404)

	def test_post_requests(self):

		# only GET is allowed on these URIs
		response = self.app.post('/api/users')
		self.assertEqual(response.status_code, 405)

		response = self.app.post('/api/users/xxx')
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

			# create a single user with a distribution and two versions
			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user', 'test user full name')")
			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 04:05:06', 'stable')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/users')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'user' : 'test_user',  'distributions' : 1, 'versions' : 2}])

		# existing distribution
		response = self.app.get('/api/users/test_user')
		self.assertEqual(response.status_code, 200)

		# unknown distribution
		response = self.app.get('/api/distributions/test_user2')
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

			# create multiple users, each with different number of distributions/versions

			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user', 'test user full name')")

			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 04:05:06', 'stable')")

			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user2', 'test user full name')")

			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr2')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 04:05:06', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.5', '2014-01-02 04:05:06', 'stable')")

			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr3')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 04:05:06', 'stable')")

			cursor.execute("INSERT INTO users (user_name, full_name) VALUES ('test_user3', 'test user full name')")

			cursor.execute("INSERT INTO distributions (user_id, dist_name) VALUES (currval('users_id_seq'), 'testdistr4')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.3', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.4', '2014-01-02 04:05:06', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.5', '2014-01-02 03:04:05', 'stable')")
			cursor.execute("INSERT INTO distribution_versions (dist_id, dist_version, dist_date, dist_status) VALUES (currval('distributions_id_seq'), '1.2.6', '2014-01-02 04:05:06', 'stable')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/users')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'user' : 'test_user', 'distributions' : 1, 'versions' : 2}, {'user' : 'test_user2', 'distributions' : 2, 'versions' : 5}, {'user' : 'test_user3', 'distributions' : 1, 'versions' : 4}])

		# existing distribution
		response = self.app.get('/api/users/test_user')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data)['info'], {'user' : 'test_user', 'distributions' : 1, 'versions' : 2})
		self.assertEqual(len(json.loads(response.data)['results']), 2)

		# second existing distribution
		response = self.app.get('/api/users/test_user2')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data)['info'], {'user' : 'test_user2', 'distributions' : 2, 'versions' : 5})
		self.assertEqual(len(json.loads(response.data)['results']), 5)

		# second existing distribution
		response = self.app.get('/api/users/test_user3')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data)['info'], {'user' : 'test_user3', 'distributions' : 1, 'versions' : 4})
		self.assertEqual(len(json.loads(response.data)['results']), 4)

if __name__ == '__main__':
	unittest.main()