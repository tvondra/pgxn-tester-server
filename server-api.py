#!/usr/bin/env python

import json
import sys

from flask import Flask
from flask.ext.restful import Api

# this is where the implementation is placed
sys.path.append('src')

from db import DB
import cors, jsonp

# create flask application
app = Flask(__name__)

# load config from the config.api dictionary
app.config.from_object('config.api')

# initialize the database pool
DB.init_pool(app.config['DATABASE'])

# create the REST api
api = Api(app)

# CORS / allow calls from all origins (well, especially pgxn-tester.org, but not only)
api.decorators=[cors.crossdomain(origin='*'), jsonp.support_jsonp]

import index
import distributions
import users
import machines
import results
import stats

api.add_resource(index.Index, '/')

api.add_resource(distributions.DistributionList, '/distributions')
api.add_resource(distributions.Distribution, 	 '/distributions/<string:name>')
api.add_resource(distributions.Version, 		 '/distributions/<string:name>/<string:version>')

api.add_resource(results.Result,	 			 '/results/<string:rid>')
api.add_resource(results.ResultList, 			 '/results')

api.add_resource(users.UserList,				 '/users')
api.add_resource(users.User,					 '/users/<string:name>')

api.add_resource(machines.MachineList, 			 '/machines')
api.add_resource(machines.Machine,	 			 '/machines/<string:name>')

api.add_resource(stats.Stats, 					 '/stats')

if __name__ == '__main__':
    app.run()
