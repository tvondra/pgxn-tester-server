# PGXN Tester API

This is API of the server part of PGXN Tester, a system tracking results of of tests of PostgreSQL extensions. It allows flexible browsing of the test results and submitting new results.

There are four basic resources, recognized by the API:

* *users*, publishing packages on [PGXN](http://pgxn.org)
* *distributions* (and versions), published at [PGXN](http://pgxn.org)
* *animals* representing machines performing tests of the distributions
* *results* representing results of the tests, submitted by the animals

Most of the API is read-only, i.e. it does not allow modification of the data. The only exception is submitting the test results and new animals.

The current API is considered an early alpha, is expected to change. It may also be used as a cautionary tale of an API designed by someone who usually works on backend systems ;-)

## Authentication

Currently the API does not provide authenticated access. Submitted results are protected by a simple signing using a shared secret.

## Media Types

Where applicable this API uses plain JSON media-type to represent resources states. Requests with a message-body are using plain JSON to set or update resource states.

## Error States

The common [HTTP Response Status Codes](http://en.wikipedia.org/wiki/Http_codes) are used.

## Distributions And Extensions

According to PGXN [definition][def], a distribution (package published at PGXN) is "... a collection of one or more PostgreSQL extensions. That’s it."

[def]: http://manager.pgxn.org/howto

Many of the distributions are package a single [extensions][extend] as defined by PostgreSQL 9.1 (this is where the "extension" in the PGXN comes from). Some distributions really contain multiple extensions, and some package tools that are not actual extensions (in the "CREATE EXTENSION" sense).

[extend]: http://www.postgresql.org/docs/9.1/static/extend-extensions.html

## Server And Animals

The server is not running any tests on it's own, it only collects and tracks results reported by other machines, and provides an API to access this data.

The machines running called *animals* - this naming is used by the official PostgreSQL [buildfarm](http://www.pgbuildfarm.org), so it was natural to reuse it for this.

There are few more elements, related to distributions and animals. For example each distribution may have multiple *versions* with various *states* (unstable, testing or stable - see [PGXN Meta Spec][spec]). Also, each distribution is associated with a *user* who published it.

[spec]: http://pgxn.org/spec/

These elements are used in the API, so it's important to understand them.


# URI Templates

## Retrive URI Templates [GET]

+ Response 200 (application/json)

        {
            'distributions' : '/distributions',
            'distribution' : '/distributions/{name}',
            'version' : '/distributions/{name}/{version}',
            'distribution-results' : '/distributions/{name}/results',
            'version-results' : '/distributions/{name}/{version}/results',
            'result' : '/results/{uuid}',
            'users' : '/users',
            'user' : '/users/{name}',
            'animal' : '/animals/{name}',
            'animals' : '/animals'
        }


# Group Users

## User [/users/{name}]

A single User object, representing an author of packages published on PGXN. It has the following attributes:

- name (login)
- distributions (number of published distributions)
- versions (number of published versions)

### Retrieve a User [GET]

+ Response 200 (application/json)

        {
            "name": "tvondra",
            "full_name" : "Tomas Vondra",
            "distributions" : 10,
            "versions" : 31
        }


## Users Collection [/users]

Collection of all Users.

### List All Users [GET]

+ Response 200 (application/json)

        [
            {
                "name": "tvondra",
                "full_name" : "Tomas Vondra",
                "distributions" : 10,
                "versions" : 31
            },
            {
                "name": "theory",
                "full_name" : "David E. Wheeler",
                "distributions" : 17,
                "versions" : 25
            },
            ...
        ]


# Group Animals

## Animal [/animals/{name}]

A single Animal object, representing a machine performing tests. It has the following attributes:

- name
- description
- active

### Retrieve a Animal [GET]

+ Response 200 (application/json)

        {
            "name": "testanimal",
            "description" : "a machine doing tests",
            "active" : true
        }


## Animals Collection [/users]

Collection of all Animals.

### List All Animals [GET]

+ Response 200 (application/json)

        [
            {
                "name": "testanimal",
                "description" : "a machine doing tests",
                "active" : true
            },
            {
                "name": "testanimal2",
                "description" : "another machine doing tests (disabled)",
                "active" : false
            },
            ...
        ]


# Group Distributions

## Distribution [/distributions/{name}]

A single Distribution object, representing a package published on PGXN, possibly with multiple versions. Each distribution has the following attributes:

- user (name of the user)
- name
- list of versions (version, date of publication, status)

### Retrieve a Distribution [GET]

+ Response 200 (application/json)

        {
            "name": "semver",
            "user" : "theory",
            "versions" : [
                {
                    "version" : "1.0.0",
                    "date" : "2014-01-02T03:04:05",
                    "status" : "stable"
                },
                {
                    "version" : "0.9.0",
                    "date" : "2013-02-03T04:05:06",
                    "status" : "testing"
                },
                {
                    "version" : "0.8.3",
                    "date" : "2012-08-12T12:13:14",
                    "status" : "unstable"
                },
                ...
            ],
            "summary" : {
                ...
            }
        }

## Distributions Collection [/distributions{?user}]

Collection of all Distributions, optionally filtered by user.

+ Parameters
    + user (optional, string) ... Name of the user. Only distributions published by this user are returned.

### List All Distributions [GET]

+ Response 200 (application/json)

        [
            {
                "name": "semver",
                "user" : "theory",
                "versions" : [
                    {
                        "version" : "1.0.0",
                        "date" : "2014-01-02T03:04:05",
                        "status" : "stable"
                    },
                    {
                        "version" : "0.9.0",
                        "date" : "2013-02-03T04:05:06",
                        "status" : "testing"
                    },
                    {
                        "version" : "0.8.3",
                        "date" : "2012-08-12T12:13:14",
                        "status" : "unstable"
                    },
                    ...
                ]
            },
            {
                "name": "pgchess",
                "user" : "gciolli",
                "versions" : [
                    {
                        "version" : "1.0.0",
                        "date" : "2014-01-02T03:04:05",
                        "status" : "stable"
                    },
                    {
                        "version" : "0.9.0",
                        "date" : "2013-02-03T04:05:06",
                        "status" : "testing"
                    },
                    {
                        "version" : "0.8.3",
                        "date" : "2012-08-12T12:13:14",
                        "status" : "unstable"
                    },
                    ...
                ]
            },
            ...
        ]


# Group Versions

## Versions [/distributions/{name}/{version}]

A single Version object, representing a version of a package published on PGXN. Each version has the following attributes:

- version number
- date of publication
- status (unstable, testing or stable)
- summary of results for this version

### Retrieve a Version [GET]

+ Response 200 (application/json)

        {
            "version" : "1.0.0",
            "date" : "2014-01-02T03:04:05",
            "status" : "stable"
        }


# Group Results

## Result [/results/{uuid}]

A single Result object, representing a test result. Each result has the following attributes:

- UUID representing the test result
- animal that reported this result
- distribution name
- version number
- date of publication
- date of the test
- result for each of stage (install, load, check)

### Retrieve a Result [GET]

+ Response 200 (application/json)

        {
            "uuid" : "88888888-8888-8888-8888-888888888888",
            "animal" : "testanimal",
            "date" : "2014-07-02T13:14:15",
            "install" : "ok",
            "load" : "error",
            "check" : "unknown",
            "logs" : {
                "install" : "...",
                "load" : "...",
                "check" : "...",
                "diff" : "...",
            }
        }

## Results Collection [/results{?animal}{?distribution}{?version}{?user}[?status}{?last}]

Collection of all Results (without detailed logs), optionally filtered by various parameters.

+ Parameters
    + animal (optional, string) ... Name of the animal, executing the test.
    + distribution (optional, string) ... Name of the distribution.
    + version (optional, string) ... Version of the distribution.
    + user (optional, string) - Name of the author of the distribution.
    + status (optional, string) - Status of the distribution (stable, testing, unstable)
    + last (optional, boolean) - If true, returns only results for last version of distributions.

### List All Distributions [GET]

+ Response 200 (application/json)

        [
            {
                "uuid" : "99999999-9999-9999-9999-999999999999",
                "animal" : "testanimal2",
                "date" : "2014-05-12T13:14:15",
                "install" : "ok",
                "load" : "ok",
                "check" : "error"
            },
            {
                "uuid" : "88888888-8888-8888-8888-888888888888",
                "animal" : "testanimal",
                "date" : "2014-07-02T13:14:15",
                "install" : "ok",
                "load" : "error",
                "check" : "unknown"
            },
            ...
        ]
