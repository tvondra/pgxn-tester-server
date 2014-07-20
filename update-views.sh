#!/usr/bin/env bash

psql "user=pgxn-tester dbname=pgxn-tester" -c "SELECT refresh_views()" > /dev/null 2>&1