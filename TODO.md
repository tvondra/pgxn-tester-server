# TODO


## API features

* better content negotiation (well, this only supports JSON, ...)
* compression of the data returned to the client (OTOH the amount of data should be small) - this should be possible / easy to implement at proxy (nginx) level
* rate limiting for submitting results (although we have only approved animals, so it's not a big problem)
* rate limiting for submitting new animals (per IP, ...), maybe protect by some sort of captcha, limit the number of animals waiting for approval or something
* rate limiting for the API as a whole (not really a good idea, let's make it scalable if needed)
* a simple "export" API, fetching all the data in a CSV format, for users doing some kind of analytics on the data (so that they don't have to struggle with the regular API)
* log durations of SQL queries (timing) for profiling purposes
* implement proper caching / set cache-related headers properly (e.g. test results are immutable, other pages are not)
* maybe a varnish cache invalidated from triggers (http://www.hagander.net/talks/Database%20driven%20cache%20invalidation.pdf) might be a good solution
* case (in)sensitivity for searches
* make sure all timestamps are in UTC and then append "Z" (for Zulu time, AKA UTC) to them. Removes ambiguity.


## UI features

* nice formatting of the install/load logs (emphasize ERROR lines)
* nice formatting of the regression diff (added/deleted lines)
* anonymization/cleanup of the logs (the logs submitted by the clients often contain specific paths etc. - not exactly confidention but probably worth removing)
* add google analytics snippet (conditionally based on configuration / custom ID)
* simple filtering in tables (e.g. of results) - e.g. by clicking on a value (or maybe an icon next to it), displaying a list of active filters (+ option to remove them)
* better links, so that it's possible to click on 'number of failed tests' in the table, and get a list of the failed results
* add a link to PGXN (to distribution, version and user)
* the API URI is hardcoded in the templates (so it can't be reused without modifying them)
* show only supported PostgreSQL versions on the front-page (and add a switch to show all)


## Detection of issues and notifications

* basic analysis of the failed builds, hinting about possible sources of issues (e.g. Makefile placed somewhere else, ...)
* sending notifications to the extension author when receiving new failures (e.g. daily, with the option to disable this using a link in the message)
* send digest of failures, not separate messages for each failure
* implement some basic checks of directory structure (Makefile in top directory, ...)


# Documentation

* improve INSTALL


# Miscellaneous

* fix and improve the tests
* consider using SSL - we're not transmitting anything confidential, but it might protect us against some basic attacks
* add twitter buttons where appropriate
* create Twitter account for news on the site, maybe regular updates (and maybe RSS for the same purpose)
* do a stress-test, to see what needs to be improved
* a simple 'status' button, people might put onto their websites or whatever (showing status of their extensions, ...) - something like a status button for travis-ci
* make the 'update-views' (or maybe refresh_views) more clever, by checking whether the timestamp of the last test changed (and do nothing if not)
