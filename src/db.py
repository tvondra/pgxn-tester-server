import psycopg2
import psycopg2.extras
import psycopg2.pool


class DB(object):
	'database context manager'

	_pool = None

	@classmethod
	def init_pool(cls, connstr):
		DB._pool = psycopg2.pool.ThreadedConnectionPool(1, 2, connstr)

	def __init__(self, readonly=True):
		self._readonly = readonly

	def __enter__(self):
		self._connection = DB._pool.getconn()
		self._connection.set_session(readonly=self._readonly, autocommit=False)
		self._cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		return (self._connection, self._cursor)

	def __exit__(self, type, value, traceback):

		# FIXME do a commit in case of read-write connection

		try:
			self._cursor.close()
		except:
			# FIXME handle the exception properly
			pass

		DB._pool.putconn(self._connection)