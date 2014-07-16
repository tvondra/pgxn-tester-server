# PGXN Tester Server

This is the server part of [PGXN Tester][ui], a tool that collects results of regression tests for distributions (packages) published at [PostgreSQL Extension Newtwork][pgxn] (aka [PGXN][pgxn]). It's inspired by the official [PostgreSQL buildfarm][buildfarm] system, which does about the same thing for PostgreSQL itself. (The are some important differences - more about that later).

[ui]: http://pgxn-tester.org

The ultimate goal of PGXN Tester is providing better tested, more reliable and less fragile distributions to PGXN users. And the first step in this direction is providing regression tests as part of the extensions, running them regularly on range of configurations and reporting the failures with all the details. Running the tests on a range of PostgreSQL versions (those supported by the distribution), various platforms etc. is very tedious, not to mention that many developers don't have easy access some of the platforms. And sometimes things breaks because of changes in the PostgreSQL core itself (e.g. when an API used by an extension is modified).

[pgxn]: http://pgxn.org
[buildfarm]: http://pgbuildfarm.org

This is the server part, i.e it only collects results of the tests, and provides them through a simple HTTP/JSON API (for other systems), and on a simple web interface (for humans). The [web interface][ui] is only a very thin layer on top of the API. If you're interested in the client (which is the part running the tests), see [pgxn-tester-client][client].

[client]: https://github.com/tvondra/pgxn-tester-client


## Issues and Limitations

The system is imperfect, and there's a lot opportunities for improvement. This sometimes results in false positives or negatives, so take the current results with a grain of salt.

At the moment, only extensions published on PGXN are tested (because we're using PGXN API and [pgxnclient][pgxnclient] to get them). It's possible that sometimes in the future this limitation will be lifted, although it's not a high priority right now.

[pgxnclient]: http://pgxnclient.projects.pgfoundry.org


## API

The provided API is based on HTTP/JSON. Although it's not 100% RESTful (and never will be), it's inspired by RESTful principles. Most of the API is read-only and uses GET requests only - the only two exceptions are submitting results (which used POST to /results), and submitting new client machine (POST to /machines).

As already mentioned, the [website][ui] is only a very simple layer on top of the API - each page requests data using a plain AJAX GET call. Also, the structure of the UI closely matches the structure of the API, and most of the time if you rewrite the URI to use api.pgxn-tester.org, you'll get the API URI executed by the page. So for example the list of users is displayed on this URI

    http://pgxn-tester.org/users

and gets the data from this API URI

    http://api.pgxn-tester.org/users

A more detailed API documentation is available in the [API.md][apidocs] file.

[apidocs]: https://github.com/tvondra/pgxn-tester-server/blob/master/API.md


## Contributing

There are various ways to help this project succeed. You may provide a machine to run the tests once in a while, or you may contribute code - fixing bugs, adding new features etc.

You may also make donations which we can use to cover the costs of running the system, and maybe do things like running tests on and AWS instance with Windows (because this OS is not really common in the community). If you're willing to make a donation, contact me directly.


## Feedback

If you need to discuss something about this site, the best way to do that by posting a message to the [pgxn-users][pgxn-users] group. You may also reach me directly at [tomas@pgaddict.com][mail].

[pgxn-users]: https://groups.google.com/d/forum/pgxn-users
[mail]: mailto:tomas@pgaddict.com


## License

The tool itself is distributed under BSD license (see LICENSE). It also uses several components that have different licenses - [Bootstrap][bootstrap], [jquery][jquery] and [flot][flot].

[bootstrap]: https://github.com/tvondra/pgxn-tester-server/blob/master/LICENSE.bootstrap
[jquery]: https://github.com/tvondra/pgxn-tester-server/blob/master/LICENSE.jquery
[flot]: https://github.com/tvondra/pgxn-tester-server/blob/master/LICENSE.flot