import flask
from flask.ext.restful import Resource, abort, reqparse

class Index(Resource):
	'list of known distributions (some may not be tested yet)'

	def get(self):
		'list of URI templates'

		# TODO this should be fetched from the API somehow (not defined in a static way)
		prefix = '/api'

		return {
			'distributions' : '/distributions',
			'distribution' : '/distributions/{name}',
			'version' : '/distributions/{name}/{version}',
			'results' : '/results',
			'result' : '/results/{uuid}',
			'users' : '/users',
			'user' : '/users/{name}',
			'animal' : '/animals/{name}',
			'animals' : '/animals',
		}
