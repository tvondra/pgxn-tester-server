# TODO

* better content negotiation (well, this only supports JSON, ...)
* compression of the data returned to the client (OTOH the amount of data should be small)
* basic analysis of the failed builds, hinting about possible sources of issues (e.g. Makefile placed somewhere else, ...)
* better dependency / prerequisities handling (currently only PostgreSQL is handled)
* somehow handling the supported platforms (e.g. Windows-only extension will fail on Linux, ...)
* sending notifications to the extension author when receiving new failures (e.g. daily, with the option to disable this using a link in the message)
* send digest of failures, not separate messages for each failure
* rate limiting for submitting results (although we have only approved animals, so it's not a big problem)
* rate limiting for submitting new animals (per IP, ...), maybe protect by some sort of captcha, limit the number of animals waiting for approval or something
* rate limiting for the API as a whole (not really a good idea, let's make it scalable if needed)
* automatic download / build of new PostgreSQL releases
* nice formatting of the install/load logs (emphasize ERROR lines)
* nice formatting of the regression diff (added/deleted lines)
* skip distributions / versions that were already tested by that animal (i.e. provide list of already performed tests, skip them in the client)
* allow '--force' in the client, to retest everything (e.g. after fixing a problem on the server configuration, ...)
* add instructions on how to operate the client with sufficient security (confine the tests within some sort of container, limit networking ...)
* implement limit on how long a test of an extension may run (e.g. to protect against infinite loops)
* a simple "export" API, fetching all the data in a CSV format, for users doing some kind of analytics on the data (so that they don't have to struggle with the regular API)
* anonymization/cleanup of the logs (the logs submitted by the clients often contain specific paths etc. - not exactly confidention but probably worth removing)
* getting additional info about the machines (env variables, uname, dmesg, ...)
* proper configuration (right now it's hardcoded in the main.py file)
* consider separating the api / ui (right now it's in the same repository etc.)
* implement some basic checks of directory structure (Makefile in top directory, ...)
* consider using SSL - we're not transmitting anything confidential, but it might protect us against some basic attacks
* add twitter buttons where appropriate
* add BSD license to github
* log durations of SQL queries (timing) for profiling purposes
* do a stress-test, to see what needs to be improved
* add google analytics snippet
* most pages miss proper paging (especially listing results)
* when listing results, allow 'failures only' mode
* the current UI does not really work with PostgreSQL releases
* implement proper caching / set cache-related headers properly (e.g. test results are immutable, other pages are not)
* a varnish cache invalidated from triggers (http://www.hagander.net/talks/Database%20driven%20cache%20invalidation.pdf) might be a good solution
* simple filtering in tables (e.g. of results) - e.g. by clicking on a value (or maybe an icon next to it), displaying a list of active filters (+ option to remove them)
* better links, so that it's possible to click on 'number of failed tests' in the table, and get a list of the failed results
* add a simple cron script, refreshing the materialied views every few minutes
* add a link to PGXN (to distribution, version and user)
* a simple 'status' button, people might put onto their websites or whatever (showing status of their extensions, ...)
* add BSD license
* case (in)sensitivity for searches