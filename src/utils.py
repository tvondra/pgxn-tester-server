import hashlib
import json

def sign_request(data, secret):
	'simple JSON signing with a shared secret'

	keys = data.keys()
	digest = hashlib.sha256()
	digest.update(secret)

	keys = sorted(data.keys())

	for k in keys:
		digest.update(k)
		digest.update(':')
		digest.update(str(data[k]))
		digest.update(';')

	return digest.hexdigest()

def verify_signature(data, secret, signature):
	'repeats the JSON signing and compares the signatures'

	signature = data['signature']

	tmp = dict((k,data[k]) for k in data if k != 'signature')

	return (sign_request(tmp, secret) == signature)

def get_pg_version(config):
	
	return json.loads(config)['VERSION'].split(' ')[1]