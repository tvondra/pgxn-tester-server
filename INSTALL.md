# Install Guide

Getting the server part work is rather trivial - I'll show what you might
do to get both API and UI running at the same host (at different ports).
And then use [nginx][nginx] as a [reverse proxy][proxy] to create two
virtual hosts (one for API, one for UI).

Of course, there are many other ways to achieve similar results - you may
use Apache instead of nginx, place the components on two different hosts
and so on. There are virtually unlimited number of possible setups.


## Prerequisities

The first thing you need to do is installing required python packages.
A great way to do that in an isolated way is [virtualenv][virtualenv]
which basically creates a separate python environment (see virtualenv
[docs][docs] for details).

Anyway, this is how to do that:

    $ virtualenv env
    $ source env/bin/activate
    (env)$ pip install -r requirements.txt

and you should be set. If you want to install the packages in a different
way, see the `requirements.txt` file for a list of packages that are needed
(currently there are only two).


# Database Configuration

OK, now we need to create a database and objects (tables, indexes). The
application is written for PostgreSQL 9.4 (yes, that's the release
still in beta - I like living on the edge). The reason for this decision
is that a lot of things is done through materialized views and 9.4 offers
REFRESH CONCURRENTLY. However it should work on 9.3 assuming you fix the
`refresh_views` function that does the refreshes.

So, let's assume you have PostgreSQL 9.4 installed and started, and create
a user and then the database. Choose whatever names you find appropriate:

    $ createuse pgxn-user
    $ createdb -O pgxn-user pgxn-db

Now you should have a new user (`pgxn-user`) and database (`pgxn-db`)
owned by the new user. Check the `createuser --help` for additional
options (e.g. disabling some privileges for the user seems like a good idea).

Finally, let's create the objects (tables, indexes, materialized views):

    $ psql -U pgxn-user pgxn-db < sql/create.sql

This assumes you have the database configured to allow password-less
access (i.e. `trust` or maybe `ident`). If that's not the case, you may
have to supply password or modify `pg_hba.conf`.


## Configuration

The database is running, so let's configure and start the Flask applications.
First, we need to tweak the config a bit - for example set connection string
to the API, etc.

Flask does this by using plain Python dictionaries, in this case placed in
`src/config.py` file. Just open it and set the keys according to the comments.

Now you should be able to start both parts - API and UI - like this (notice
that you need to be in the virtual environment, created at the beginning):

    (env)$ ./server-api.py
    ...

    (env)$ ./server-ui.py
    ...
    
Now try to connect to `localhost:6000` and you should see the UI (without
any data, of course).


## Nginx Reverse Proxy

The last step is attaching the two applications to the right virtualhosts
using nginx. One way to do that is like this, which redirects the 'api'
subdomain to port 5000 and UI (no subdomain) to port 6000. Of course, this
needs to match the Flask configuration (that's where the ports are
specified too).

    server {

            listen 127.0.0.1;
            server_name api.pgxn-tester.org;

            access_log /var/log/nginx/api.access_log main;
            error_log /var/log/nginx/api.error_log info;

            location / {
                    proxy_pass http://127.0.0.1:5000;
            }

    }

    server {

            listen 127.0.0.1;
            server_name pgxn-tester.org;

            access_log /var/log/nginx/web.access_log main;
            error_log /var/log/nginx/web.error_log info;

            location / {
                    proxy_pass http://127.0.0.1:6000;
            }

    }

Again, consult [nginx][nginx] documentation for more details.

Of course, this only works locally (as it attaches the servers to localhost).
That's OK for development, but if you want to make the applications public
you need to change the IP. And probably the server names too, to domains
operated by you.

*Note*: One note though. The current UI hardcodes the API URIs in the templates,
so to make that work you need to fix this (a simple `sed` in `templates` directory
should fix that). Fixing this is on the TODO list, although not with very high
priority.

[nginx]: http://nginx.org/
[proxy]: http://en.wikipedia.org/wiki/Reverse_proxy
[virtualenv]: https://pypi.python.org/pypi/virtualenv
[docs]: http://virtualenv.readthedocs.org/en/latest/
