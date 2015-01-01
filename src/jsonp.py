import json
import re

from functools import wraps
from flask import redirect, request, current_app

def support_jsonp(f):
	"""Wraps JSONified output for JSONP"""

	@wraps(f)
	def decorated_function(*args, **kwargs):

		callback = request.args.get('callback', False)

		# sanitize the callback names
		if callback and not re.match('^pgxn_[a-zA-Z0-9_]+$', str(callback)):
			callback = None

		if callback:
			content = str(callback) + '(' + str(f(*args,**kwargs).data).strip() + ')'
			return current_app.response_class(content, mimetype='application/javascript')
		else:
			return f(*args, **kwargs)

	return decorated_function
