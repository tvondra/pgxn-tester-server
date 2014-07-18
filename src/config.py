
# configuration for the API
api = dict(

	# change to False on production
	DEBUG = True,

	# change to sufficiently long random value
	SECRET_KEY = "SSAK0JHIV1HG18K80YwqzWFFPWizaa88",
	
	# obvious meaning (depends on your reverse proxy config etc.)
	SERVER_NAME = "localhost:5000",

	# PostgreSQL connection string
	DATABASE = 'host=... user=... dbname=... port=...',

)

# configuration for the UI
ui = dict(

	# change to False on production
	DEBUG = True,

	# change to sufficiently long random value
	SECRET_KEY = "9JrUjEYMLTMdhvMBGsFBvLUohaPe29K8",
	
	# obvious meaning (depends on your reverse proxy config etc.)
	SERVER_NAME = "localhost:6000",

)