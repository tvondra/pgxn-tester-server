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
			cursor.execute("TRUNCATE animals CASCADE")
			cursor.execute("TRUNCATE users CASCADE")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/animals')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [])

		# unknown distribution
		response = self.app.get('/api/animals/xxx')
		self.assertEqual(response.status_code, 404)


class TestSingleAnimal(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE animals CASCADE")

			# create a single user with a distribution and two versions
			cursor.execute("INSERT INTO animals (animal_name, animal_secret, animal_email) VALUES ('test_animal', 'animal secret', 'animal email')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/animals')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'name' : 'test_animal',  'distributions' : 0, 'versions' : 0, 'tests' : 0}])

		# existing distribution
		response = self.app.get('/api/animals/test_animal')
		self.assertEqual(response.status_code, 200)

		# unknown distribution
		response = self.app.get('/api/animals/test_animal2')
		self.assertEqual(response.status_code, 404)


class TestMultipleAnimals(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE animals CASCADE")

			# animal #1
			cursor.execute("INSERT INTO animals (animal_name, animal_secret, animal_email) VALUES ('test_animal', 'animal secret', 'animal email')")

			# animal #2
			cursor.execute("INSERT INTO animals (animal_name, animal_secret, animal_email) VALUES ('test_animal2', 'animal secret', 'animal email')")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_get_requests(self):

		# list distributions (there are none)
		response = self.app.get('/api/animals')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), [{'name' : 'test_animal', 'distributions' : 0, 'versions' : 0, 'tests' : 0}, {'name' : 'test_animal2', 'distributions' : 0, 'versions' : 0, 'tests' : 0}])

		# existing distribution
		response = self.app.get('/api/animals/test_animal')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data)['info'], {'name' : 'test_animal', 'distributions' : 0, 'versions' : 0, 'tests' : 0})

		# second existing distribution
		response = self.app.get('/api/animals/test_animal2')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data)['info'], {'name' : 'test_animal2', 'distributions' : 0, 'versions' : 0, 'tests' : 0})


class TestAnimalPost(unittest.TestCase):
	'test basic response with empty database'

	@classmethod
	def setUpClass(cls):

		app.config['DATABASE'] = config.connstr
		app.config['TESTING'] = True

		DB.init_pool(app.config['DATABASE'])

		with DB(False) as (conn, cursor):

			# this pretty much cascades to everything, except animals
			cursor.execute("TRUNCATE animals CASCADE")

			conn.commit()

	def setUp(self):
		self.app = app.test_client()

	def test_correct_post(self):

		result = {	"name" : "testanimal",
					"description" : "animal description",
					"email" : "animal email"
				}

		# list distributions (there are none)
		response = self.app.post('/api/animals', data=json.dumps(result), content_type='application/json')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.data), {'result' : 'OK'})

if __name__ == '__main__':
	unittest.main()