#!/usr/bin/python

import json
import sys

from flask import Flask, render_template, request

app = Flask(__name__, instance_relative_config=True)

sys.path.append('src')

# load config from the config.ui dictionary
app.config.from_object('config.ui')

@app.route('/')
def summary_page():
	return render_template('index.html')

@app.route('/users')
def users_page():
	return render_template('users.html', title='Users')

@app.route('/users/<name>')
def user_page(name=None):
	return render_template('user.html', user=name, title=name)

@app.route('/machines')
def animals_page():
	return render_template('machines.html', title='Machines')

@app.route('/machines/<name>')
def animal_page(name=None):
	return render_template('machine.html', machine=name, title=name)

@app.route('/distributions')
def distributions():
	return render_template('distributions.html', title='Distributions')

@app.route('/distributions/<name>')
def distribution(name=None):
	return render_template('distribution.html', distribution=name, title=name)

@app.route('/distributions/<name>/<version>')
def version(name=None, version=None):
	return render_template('version.html', distribution=name, version=version, title="-".join([name, version]))

@app.route('/results')
def results_page():
	return render_template('results.html', title='Results', filters={str(name) : str(request.args[name]) for name in request.args})

@app.route('/results/<uid>')
def result_page(uid):
	return render_template('result.html', uuid=uid, title=uid)

@app.route('/trends')
def trends_page():
	return render_template('trends.html', title='Trends')

@app.route('/about')
def about_page():
	return render_template('about.html', title='About')

if __name__ == '__main__':
	app.run()
