from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

# Decorator that adds 'CORS' headers, allowing browsers to call the API
# from different domains (this is meant to be a public API, so why not).

def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attach_to_all=True, automatic_options=True):

	# only allow some methods (GET, POST, ... or all)
	if methods is not None:
		methods = ', '.join(sorted(x.upper() for x in methods))

	# send additional headers
	if headers is not None and not isinstance(headers, basestring):
		headers = ', '.join(x.upper() for x in headers)

	# which origins to allow
	if not isinstance(origin, basestring):
		origin = ', '.join(origin)

	# caching limit
	if isinstance(max_age, timedelta):
		max_age = max_age.total_seconds()

	# which methods are allowed?
	def get_methods():

		# if we have specified methods, return the list
		if methods is not None:
			return methods

		# return default OPTIONS response
		options_resp = current_app.make_default_options_response()
		return options_resp.headers['allow']

	# method implementing the URI decorator (wraps a function, adding CORS headers)
	def decorator(f):

		def wrapped_function(*args, **kwargs):

			if automatic_options and request.method == 'OPTIONS':
				resp = current_app.make_default_options_response()
			else:
				resp = make_response(f(*args, **kwargs))
			if not attach_to_all and request.method != 'OPTIONS':
				return resp

			h = resp.headers

			h['Access-Control-Allow-Origin'] = origin
			h['Access-Control-Allow-Methods'] = get_methods()
			h['Access-Control-Max-Age'] = str(max_age)
			if headers is not None:
				h['Access-Control-Allow-Headers'] = headers
			return resp

		f.provide_automatic_options = False
		return update_wrapper(wrapped_function, f)

	return decorator