# PGXN Tester API

The API provided by pgxn-tester-server is a simple HTTP/JSON API. It's inspired by RESTful principles but is not (and never will be) 100% RESTful compliant (whatever that means). Most of the API is read-only, i.e. it only allows GET requests and does not modify the data. The only exception is submitting the test results and new animals.

The current API is considered an early alpha, is expected to change. It may also be used as a cautionary tale of an API designed by someone who usually works on backend systems ;-)


## Authentication

Currently the API does not provide any authenticated access (and there are no plans to add it, as it's not necessary). Submitted results are protected by a simple signing by a shared secret.


## Media Types

Where applicable this API uses plain JSON media-type to represent resources states. Requests with a message-body are using plain JSON to set or update resource states (e.g. to post test results).


## Error States

The common [HTTP Response Status Codes](http://en.wikipedia.org/wiki/Http_codes) are used.


## Resources

The API provides access to four (or maybe five) resources, and understanding how they relate is important for understanding the API. 


### Distributions

Distributions are packages published at [PGXN][pgxn], and typically contain code extending the PostgreSQL database - e.g. by providing new datatypes (see for example [sha][sha] or [pgmp][pgmp]), aggregate functions (e.g. [weighted_mean][weighted_mean]) and so on.

[sha]: http://pgxn.org/dist/sha/
[pgmp]: http://pgxn.org/dist/pgmp/
[weighted_mean]: http://pgxn.org/dist/weighted_mean

Actually, what gets published is not a distribution, but a "version of a distribution." See for example [semver][semver] which already publishes multiple versions. This is very similar to packaging systems like `rpm` or `yum` where by installing a package you actually install a specific version of the package. You may either consider "version" to be a separate resource (in that case there are five), or simply use distributions in both cases - the meaning is usually clear from context. For example by "testing a distribution" you probably mean "testing a version of a distribution."

[semver]: http://pgxn.org/dist/semver/

One common misconception is that distributions are only nicely packaged [extensions][extend] (i.e. code that gets installed using [CREATE EXTENSION][create-extension] from the database). That's usually the case, however the distributions may package different kinds of code (e.g. tools that are not meant to add pieces into the database but rather provide external tools - like for example [omnipitr][omnipitr] providing nice PITR-related tools).

In some cases the mapping may not be 1:1, as a single distribution may include multiple extensions (see the [META.json][meta] specification, showing that [pgTAP][pgtap] actually provides two extensions - `pgtap` and `schematap`).

[create-extension]: http://www.postgresql.org/docs/9.4/static/sql-createextension.html
[omnipitr]: http://pgxn.org/dist/omnipitr/
[meta]: http://pgxn.org/spec/
[pgtap]: http://pgxn.org/dist/pgtap/
[extend]: http://www.postgresql.org/docs/9.1/static/extend-extensions.html

One final detail - each version has a "status" identifying the stage of the development. There are three allowed values - unstable, testing and stable (with rather obvious meanings).


### Users

This is really trivial - users are authors of distributions, publishing them at [PGXN][pgxn]. Each user has a nick (login) and full name.


### Machines

These are the machines running the regression tests and reporting the results to the server (as explained in the [README]). The machines are tunning [pgxn-tester-client][client] that installs the extensions, runs the tests and then reports the results to the server. Each machine has a name, secret key (used to sign the results) and a few other properties.

[README]: https://github.com/tvondra/pgxn-tester-server/blob/master/README.md
[client]: https://github.com/tvondra/pgxn-tester-client

The official PostgreSQL [buildfarm](http://www.pgbuildfarm.org) calls the machines "animals" and gives them animal names (e.g. "hamster" or "sloth"), but to avoid confusion we've sticked with the generic "machine" naming scheme, and using names of [psychotic computers][psycho] which seems perfectly appropriate for machines running regression tests.

[psycho]: http://namingschemes.com/Psychotic_Computers


### Results

In short a heap of information describing the results of the tests. It says whether the installation was successful (compiling the code, installing into database, ...), whether the regression tests passes, logs for each of the phases and basic info about the environment (to simplify the debugging).

[pgxn]: http://pgxn.org


### Summary Results

TODO explain how a summary of results (for version / distribution / user / machine is tested).


## URI Templates

The system URI templates, as explained in [RFC 6570][rfc]. To get the templates just access the root URI of the API (e.g. http://api.pgxn-tester.org).

[rfc]: http://tools.ietf.org/html/rfc6570

### Retrive URI Templates [GET]

+ Response 200 (application/json)

        {
            "distribution": "/distributions/{name}", 
            "distributions": "/distributions", 
            "machine": "/machines/{name}", 
            "machines": "/machines", 
            "result": "/results/{uuid}", 
            "results": "/results", 
            "user": "/users/{name}", 
            "users": "/users", 
            "version": "/distributions/{name}/{version}"
        }

## Users
    
### User [/users/{name}]

A single User object, representing an author of packages published on PGXN. It has the following attributes:

- name (login)
- full name
- number of published distributions
- number of published versions
- distributions, mapping the name to an array of versions
- for each version there's a summary of test results (for each phase)

I.e. it's somewhat more detailed than the list of users.


#### Retrieve a User [GET]

+ Response 200 (application/json)

        {
            "info": {
                "distributions": 15, 
                "name": "Tomas Vondra", 
                "user": "tomasv", 
                "versions": 47
            },
            "distributions": {
                "adaptive_estimator": [
                    {
                        "check": {
                            "error": 11, 
                            "missing": 0, 
                            "ok": 44
                        }, 
                        "date": "2014-04-27T01:19:47", 
                        "install": {
                            "error": 0, 
                            "ok": 55
                        }, 
                        "load": {
                            "error": 0, 
                            "ok": 55
                        }, 
                        "status": "testing", 
                        "version": "1.3.1"
                    },
                    ... more versions ...
                ],
                ... more distributions ...
            }
        }

### Users Collection [/users]

Collection of all users. Compared to the single-user response, there are no detailed information about published distributions (or versions), but only a summary of results.

#### List All Users [GET]

+ Response 200 (application/json)

        [
            {
                "name": "alexk", 
                "full_name": "Alexey Klyukin", 
                "distributions": 7, 
                "versions": 12,
                "check": {
                    "error": 190, 
                    "missing": 88, 
                    "ok": 0
                }, 
                "install": {
                    "error": 17, 
                    "ok": 308
                }, 
                "load": {
                    "error": 30, 
                    "ok": 278
                }
            },
            ... more users ...
        ]


## Machines

### Machine [/machines/{name}]

A single Machine object, representing a machine performing tests. It has the following attributes:

- name
- description
- active flag
- date of the most recent test
- number of tests executed
- number of distributions tested
- number of versions tested
- summary of results (per PostgreSQL major version and version status)
- list of tested distributions (for each version, there's a list of PostgreSQL minor / full versions from executed tests)

#### Retrieve a Machine [GET]

+ Response 200 (application/json)
    
        {
            "info": {
                "description": null, 
                "distributions": 105, 
                "is_active": true, 
                "last_test_date": "2014-07-15T20:48:59", 
                "name": "hal-9000", 
                "tests": 5234, 
                "versions": 407
            }, 
            "stats": {
                "9.4": {
                    "stable": {
                        "check": {
                            "error": 8, 
                            "missing": 15, 
                            "ok": 10
                        }, 
                        "install": {
                            "error": 36, 
                            "ok": 34
                        }, 
                        "load": {
                            "error": 1, 
                            "ok": 33
                        }
                    }, 
                    ... other version statuses ...
                },
                ... other PostgreSQL major versions ...
            },
            "tested": {
                "CyanAudit": {
                    "0.9.0": {
                        "major": [
                            "9.4",
                            "9.1",
                            "9.2",
                            "9.3"
                        ],
                        "minor": [
                            "9.1.13",
                            "9.4beta1",
                            "9.2.8",
                            "9.3.4"
                        ]
                    },
                    ... more versions ...
                },
                ...  more distributions ...
            }
        }



### Machine Queue [/machines/{name}]

A list of distribution versions that need to be tested on a particular machine. Returns a simple array of (name,version) pairs:

- distribution name
- version number

#### Retrieve a Machine Queue [GET]

+ Response 200 (application/json)
    
        [
            {
                "name": "citext", 
                "version": "2.0.1"
            }, 
            {
                "name": "superloglog_estimator", 
                "version": "1.2.2"
            }
        ]


### Machines Collection [/machines]

Collection of all Machines, again with a simplified summary of test results.

#### List All Machines [GET]

+ Response 200 (application/json)

        [
            {
                "check": {
                    "error": 99, 
                    "missing": 113, 
                    "ok": 95
                }, 
                "distributions": 105, 
                "install": {
                    "error": 289, 
                    "ok": 330
                }, 
                "is_active": true, 
                "last_test_date": "2014-07-15T20:03:20", 
                "load": {
                    "error": 23, 
                    "ok": 307
                }, 
                "name": "deep-thought", 
                "tests": 2914, 
                "versions": 407
            },
            ... more machines ...
        ]


## Distributions

### Distribution [/distributions/{name}]

A single Distribution object, representing a package published on PGXN, possibly with multiple versions. Each distribution has the following attributes:

- name of the distribution
- user (name of the user)
- summary per release status (last version for that status considered)
- list of versions (version, date of publication, status, prerequisities, summary of results)
- the list of versions may be disabled by adding ?details=0 to the URI

#### Retrieve a Distribution [GET]

+ Response 200 (application/json)
    
        {
            "name": "aclexplode", 
            "user": "alexk",
            "summary" : {
                "stable" : {
                    "check": {
                        "error": 66, 
                        "missing": 0, 
                        "ok": 0
                    }, 
                    "date": "2012-09-21T16:51:39", 
                    "install": {
                        "error": 11, 
                        "ok": 66
                    }, 
                    "load": {
                        "error": 0, 
                        "ok": 66
                    }, 
                },
                ... testing, unstable ...
            },
            "versions": [
                {
                    "check": {
                        "error": 66, 
                        "missing": 0, 
                        "ok": 0
                    }, 
                    "date": "2012-09-21T16:51:39", 
                    "install": {
                        "error": 11, 
                        "ok": 66
                    }, 
                    "load": {
                        "error": 0, 
                        "ok": 66
                    }, 
                    "prereqs": [
                        "8.3.0"
                    ], 
                    "status": "stable", 
                    "version": "1.0.3"
                },
                ... more versions ...
            ]
        }

### Distributions Collection [/distributions]

Collection of all Distributions, optionally filtered by user (author).

+ Parameters
    + user (optional, string) ... Name of the user. When supplied, only distributions published by this user are returned.

#### List All Distributions [GET]

+ Response 200 (application/json)
    
        [
            {
                "check": {
                    "error": 66, 
                    "missing": 0, 
                    "ok": 0
                }, 
                "install": {
                    "error": 11, 
                    "ok": 66
                }, 
                "load": {
                    "error": 0, 
                    "ok": 66
                }, 
                "name": "aclexplode", 
                "user": "alexk"
            },
            ...
        ]


## Versions

### Versions [/distributions/{name}/{version}]

A single Version object, representing a version of a package published on PGXN. Each version has the following attributes:

- version number
- date of publication
- status (unstable, testing or stable)
- summary of results of this version (all machines / PostgreSQL major versions combined)
- detailed summary of results for this version (from each combination of machine / PostgreSQL major version)
- the detailed summary may be disabled by adding ?details=0 to the URI
- prerequisities of the version (extracted from META.json)

#### Retrieve a Version [GET]

+ Response 200 (application/json)
    
        {
            "abstract": "", 
            "date": "2012-09-21T16:51:39Z", 
            "description": "", 
            "name": "aclexplode", 
            "status": "stable", 
            "summary": {
                "check": {
                    "error": 0, 
                    "missing": 0, 
                    "ok": 18
                }, 
                "install": {
                    "error": 0, 
                    "ok": 18
                }, 
                "load": {
                    "error": 0, 
                    "ok": 18
                }
            }, 
            "user": "alexk", 
            "version": "1.0.3",
            "stats": {
                "deep-thought": [
                    {
                        "check": "error", 
                        "date": "2014-07-15T13:45:14", 
                        "install": "ok", 
                        "load": "ok", 
                        "uuid": "63f6984b-299c-4a19-8932-24f4a93c3f12", 
                        "version": "9.4"
                    }, 
                    {
                        "check": "", 
                        "date": "2014-07-15T11:46:10", 
                        "install": "error", 
                        "load": "", 
                        "uuid": "12c106ad-c352-412c-ab69-1460af04d04b", 
                        "version": "9.3"
                    },
                    ... more results from this machine ...
                ],
                ... more machines ...
            }
        }

### Versions Collection

There's no separate URI to get collection of versions, apart from through distribution [/distributions/{name}].


## Group Results

### Result [/results/{uuid}]

A single Result object, representing a test result. Each result has the following attributes:

- UUID identifying the test result
- distribution name
- version number
- date of publication
- date of the test
- PostgreSQL version
- user publishing the distribution
- machine that reported this result
- result for each of phase (install, load, check)
- duration for each phase (install, load, check)
- logs for each phase (install, load, check)
- regression diff for the check phase
- pg_config and environment variables

#### Retrieve a Result [GET]

+ Response 200 (application/json)
    
        {
            "uuid": "3dd29fe0-a815-4fb0-bf12-f922c1e3d2fa", 
            "dist": "plparrot",
            "version": "0.4.0"
            "state": "stable", 
            "date": "2011-07-24T08:09:25", 
            "test_date": "2014-07-15T20:48:59", 
            "pg_version": "9.2.8", 
            "user": "dukeleto", 
            "machine": "hal-9000", 
            "install_result": "error", 
            "load_result": null, 
            "check_result": null, 
            "log_install": ... log from `pgxnclient install` ..., 
            "log_load": ... log from `pgxnclient load` ..., 
            "log_check": ... log from `pgxnclient check` ..., 
            "check_diff": ... diff for the regression test ..., 
            "install_duration": 1698, 
            "load_duration": 0, 
            "check_duration": 0, 
            "env_info": { ... environment variables ...}, 
            "pg_config": {
                "BINDIR": "/home/tomas/work/pgxn-tester/pg/postgresql-9.2.8/bin", 
                "CC": "gcc", 
                "VERSION": "PostgreSQL 9.2.8",
                ... more config variables ...
            },
        }

### Results Collection [/results]

Collection of all Results (without detailed logs etc.), optionally filtered by various parameters. Returns 50 items (use `date` parameter for simple paging).

+ Parameters
    + machine (optional, string) ... Name of the machine, executing the test.
    + distribution (optional, string) ... Name of the distribution.
    + version (optional, string) ... Version of the distribution.
    + user (optional, string) - Name of the author of the distribution.
    + status (optional, string) - Status of the distribution (stable, testing, unstable)
    + last (optional, boolean) - If true, returns only results for last version of distributions.
    + pg (optional, string) - PostgreSQL major version
    + pg_version (optional, string) - PostgreSQL version (exact)
    + date (optional, date) - date of reporting the result (only results older than this date are reported)

#### List All Distributions [GET]

+ Response 200 (application/json)

        [
            {
                "check": null, 
                "dist": "plparrot", 
                "install": "error", 
                "load": null, 
                "machine": "hal-9000", 
                "pg_version": "9.2.8", 
                "status": "stable", 
                "test_date": "2014-07-15T20:48:59", 
                "user": "dukeleto", 
                "uuid": "3dd29fe0-a815-4fb0-bf12-f922c1e3d2fa", 
                "version": "0.4.0", 
                "version_date": "2011-07-24T08:09:25"
            }, 
            {
                "check": null, 
                "dist": "planinstr", 
                "install": "error", 
                "load": null, 
                "machine": "hal-9000", 
                "pg_version": "9.2.8", 
                "status": "unstable", 
                "test_date": "2014-07-15T20:48:57", 
                "user": "umitanuki", 
                "uuid": "5173cb77-5446-4335-bc0e-f90a8d64cbfb", 
                "version": "0.0.1", 
                "version_date": "2011-06-14T06:52:45"
            },
            ... more results ...
        ]
