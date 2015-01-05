import hashlib
import json

from pgxnclient.utils.semver import SemVer

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


def extract_prereqs(meta):
	'''extract prerequisities (required PostgreSQL versions) from META'''

	prereqs = []

	if (meta is None) or ('prereqs' not in meta):
		return []

	for prereq_type in ['configure', 'build', 'test', 'runtime']:
		if prereq_type in meta['prereqs']:
			if 'requires' in meta['prereqs'][prereq_type]:
				for v in meta['prereqs'][prereq_type]['requires']:
					prereqs.append({v : meta['prereqs'][prereq_type]['requires'][v]})

	# extract only PostgreSQL-related prerequisities
	return [v['PostgreSQL'] for v in prereqs if ('PostgreSQL' in v)]


def check_prereqs(pgversion, prereqs):
	'verifies requirements on PostgreSQL version'

	for prereq in prereqs:
		tmp = [v.strip() for v in prereq.split(',')]
		for r in tmp:
			res = re.match('(>|>=|=|==|<=|<)?(\s+)?([0-9]+\.[0-9]+\.[0-9]+)', r)
			if res:
				operator = res.group(1)
				version = SemVer(res.group(3))

				if (operator is None) or (operator == '>='):
					if not (pgversion >= version):
						return False
				elif (operator == '=') or (operator == '=='):
					if not (pgversion == version):
						return False
				elif (operator == '>'):
					if not (pgversion > version):
						return False
				elif (operator == '>='):
					if not (pgversion >= version):
						return False
				elif (operator == '<'):
					if not (pgversion < version):
						return False
				elif (operator == '<='):
					if not (pgversion <= version):
						return False
				else:
					print "unknown operator in prerequisity:",r

			else:
				print "skipping invalid prerequisity :",r

	return True