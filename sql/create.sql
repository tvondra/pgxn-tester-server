-- a function producing simple JSON compatible ISO timestamp
CREATE OR REPLACE FUNCTION isodate(timestamp) RETURNS text AS $$
SELECT to_char($1, 'YYYY-MM-DD"T"HH24:MI:SS')
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION major_version(text) RETURNS text AS $$
SELECT substring($1 from '^[0-9]+\.[0-9]+')
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION random_string(p_len INT = 32) RETURNS text AS $$
DECLARE
    v_int INT;
    v_string TEXT := '';
    v_characters TEXT := '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
BEGIN

    WHILE (length(v_string) < p_len) LOOP
        v_string := v_string || substr(v_characters, (random() * length(v_characters))::int, 1);
    END LOOP;

    return v_string;
    
END;
$$ LANGUAGE plpgsql;

-- users
CREATE TABLE users (

    id         SERIAL PRIMARY KEY,

    -- PGXN username
    user_name  TEXT NOT NULL UNIQUE,
    full_name  TEXT NOT NULL

);

-- distributions (packages)
CREATE TABLE distributions (

    id         SERIAL PRIMARY KEY,

    -- author of the distribution
    user_id    INT NOT NULL REFERENCES users(id),

    -- PGXN distributions
    dist_name  TEXT NOT NULL UNIQUE

);

-- package versions
CREATE TABLE distribution_versions (

    id              SERIAL PRIMARY KEY,

    -- which distribution is this?
    dist_id         INT NOT NULL REFERENCES distributions(id),

    -- version number (possibly semver?)
    version_number  TEXT NOT NULL,
    version_date    TIMESTAMP NOT NULL,

    -- replace by proper enum
    version_status  TEXT NOT NULL,

    -- META (needed because of prerequisities)
    version_meta    JSON NOT NULL

);

-- machines doing the tests
CREATE TABLE machines (

    id              SERIAL PRIMARY KEY,

    name            TEXT NOT NULL UNIQUE,
    secret_key      TEXT NOT NULL DEFAULT random_string(32),

    -- description, contact e-mail etc.
    description     TEXT,
    contact_email   TEXT NOT NULL,

    -- all machines need to be approved first
    is_approved     BOOLEAN NOT NULL DEFAULT false,

    -- false => deleted, disabled machines
    is_active       BOOLEAN NOT NULL DEFAULT true

);

CREATE TYPE test_result AS ENUM ('ok', 'error', 'missing');

CREATE TABLE results (

    id              SERIAL PRIMARY KEY,

    -- public ID of the result (random UUID)
    result_uuid     TEXT NOT NULL UNIQUE,

    machine_id      INT NOT NULL REFERENCES machines(id),
    dist_version_id INT NOT NULL REFERENCES distribution_versions(id),

    -- when was the result submitted
    submit_date     TIMESTAMP NOT NULL DEFAULT now(),

    -- version of PostgreSQL
    pg_version      TEXT NOT NULL,

    -- pg_config output (info about CFLAGS etc.)
    pg_config       JSON NOT NULL,

    -- various info about environment (e.g. 'uname -a' and whatever the client considers useful)
    env_info        JSON NOT NULL,

    -- results of each phase
    load_result     test_result,
    install_result  test_result,
    check_result    test_result,

    -- duration of steps (in miliseconds)
    load_duration       INT,
    install_duration    INT,
    check_duration      INT,

    -- log from each phase (if available), and a diff from the pg_regress check
    log_load        TEXT,
    log_install     TEXT,
    log_check       TEXT,
    check_diff      TEXT

);

CREATE INDEX results_version_idx ON results (dist_version_id);
CREATE INDEX results_machine_idx ON results (machine_id);
CREATE INDEX distribution_version_idx ON distribution_versions(dist_id);
CREATE INDEX distributions_user_idx ON distributions(user_id);

-- ID of the last result for each distribution/machine/major_version
CREATE MATERIALIZED VIEW results_last
    AS SELECT DISTINCT machine_id, dist_version_id, major_version(pg_version) AS pg_version,
                       LAST_VALUE(id)
                           OVER (PARTITION BY machine_id, major_version(pg_version), dist_version_id
                                 ORDER BY submit_date ASC
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS result_id
  FROM results;

CREATE UNIQUE INDEX results_last_id_idx ON results_last (result_id);
CREATE INDEX results_last_machine_idx ON results_last (machine_id);
CREATE INDEX results_last_version_idx ON results_last (dist_version_id);

-- ID of the last version for distribution/status
CREATE MATERIALIZED VIEW version_last
    AS SELECT DISTINCT dist_id, version_status,
                       LAST_VALUE(id)
                           OVER (PARTITION BY dist_id, version_status
                           ORDER BY version_date ASC
                           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS version_id
  FROM distribution_versions;

CREATE UNIQUE INDEX version_last_idx ON version_last(dist_id, version_status);

-- summary of the last version (per state) and last test (from each machine / per version)
CREATE MATERIALIZED VIEW results_summary
    AS SELECT
        rl.pg_version,
        version_status AS status,
        COUNT (CASE WHEN install_result = 'ok' THEN 1 END) AS install_ok,
        COUNT (CASE WHEN install_result = 'error' THEN 1 END) AS install_error,
        COUNT (CASE WHEN load_result = 'ok' THEN 1 END) AS load_ok,
        COUNT (CASE WHEN load_result = 'error' THEN 1 END) AS load_error,
        COUNT (CASE WHEN check_result = 'ok' THEN 1 END) AS check_ok,
        COUNT (CASE WHEN check_result = 'error' THEN 1 END) AS check_error,
        COUNT (CASE WHEN check_result = 'missing' THEN 1 END) AS check_missing
    FROM results r JOIN results_last rl ON (r.id = rl.result_id)               -- only last result from each machine/distribution/version
                   JOIN version_last vl ON (r.dist_version_id = vl.version_id) -- only last version for each distribution/state
    GROUP BY 1, 2 ORDER BY 1, 2;

CREATE UNIQUE INDEX results_summary_idx ON results_summary(pg_version, status);

-- result summary per version and last test (from each machine)
CREATE MATERIALIZED VIEW results_version
    AS SELECT
        rl.dist_version_id,
        COUNT (CASE WHEN install_result = 'ok' THEN 1 END) AS install_ok,
        COUNT (CASE WHEN install_result = 'error' THEN 1 END) AS install_error,
        COUNT (CASE WHEN load_result = 'ok' THEN 1 END) AS load_ok,
        COUNT (CASE WHEN load_result = 'error' THEN 1 END) AS load_error,
        COUNT (CASE WHEN check_result = 'ok' THEN 1 END) AS check_ok,
        COUNT (CASE WHEN check_result = 'error' THEN 1 END) AS check_error,
        COUNT (CASE WHEN check_result = 'missing' THEN 1 END) AS check_missing
    FROM results_last rl JOIN results r ON (r.id = rl.result_id) -- only last result from each machine/distribution/version
    GROUP BY 1 ORDER BY 1;

CREATE UNIQUE INDEX results_version_unique_idx ON results_version(dist_version_id);

-- result summary per distribution and last test (from each machine) / last version
CREATE MATERIALIZED VIEW results_distribution
    AS SELECT
        vl.dist_id,
        COUNT (CASE WHEN install_result = 'ok' THEN 1 END) AS install_ok,
        COUNT (CASE WHEN install_result = 'error' THEN 1 END) AS install_error,
        COUNT (CASE WHEN load_result = 'ok' THEN 1 END) AS load_ok,
        COUNT (CASE WHEN load_result = 'error' THEN 1 END) AS load_error,
        COUNT (CASE WHEN check_result = 'ok' THEN 1 END) AS check_ok,
        COUNT (CASE WHEN check_result = 'error' THEN 1 END) AS check_error,
        COUNT (CASE WHEN check_result = 'missing' THEN 1 END) AS check_missing
    FROM results_last rl JOIN results r ON (r.id = rl.result_id) -- only last result from each machine/distribution/version
                         JOIN version_last vl ON (vl.version_id = r.dist_version_id)
    GROUP BY 1 ORDER BY 1;

CREATE UNIQUE INDEX results_distribution_idx ON results_distribution(dist_id);

-- result summary per machine and last test (last version)
CREATE MATERIALIZED VIEW results_machine
    AS SELECT
        rl.machine_id,
        rl.pg_version,
        version_status AS status,
        COUNT (CASE WHEN install_result = 'ok' THEN 1 END) AS install_ok,
        COUNT (CASE WHEN install_result = 'error' THEN 1 END) AS install_error,
        COUNT (CASE WHEN load_result = 'ok' THEN 1 END) AS load_ok,
        COUNT (CASE WHEN load_result = 'error' THEN 1 END) AS load_error,
        COUNT (CASE WHEN check_result = 'ok' THEN 1 END) AS check_ok,
        COUNT (CASE WHEN check_result = 'error' THEN 1 END) AS check_error,
        COUNT (CASE WHEN check_result = 'missing' THEN 1 END) AS check_missing
    FROM results r JOIN results_last rl ON (r.id = rl.result_id)               -- only last result from each machine/distribution/version
                   JOIN version_last vl ON (rl.dist_version_id = vl.version_id) -- only last version for each distribution/state
    GROUP BY 1, 2, 3 ORDER BY 1, 2, 3;

CREATE UNIQUE INDEX results_machine_unique_idx ON results_machine(machine_id, status, pg_version);

-- result summary per machine and last test (last version)
CREATE MATERIALIZED VIEW results_version_details
    AS SELECT
        r.id AS result_id,
        rl.machine_id,
        rl.pg_version,
        r.dist_version_id,
        install_result AS install,
        load_result AS load,
        check_result AS "check"
    FROM results r JOIN results_last rl ON (r.id = rl.result_id)               -- only last result from each machine/distribution/version
    ORDER BY 1, 2, 3;

CREATE UNIQUE INDEX results_versio_details_idx ON results_version_details(result_id);

-- refresh all the views with current info
CREATE OR REPLACE FUNCTION refresh_views() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_last;
    REFRESH MATERIALIZED VIEW CONCURRENTLY version_last;
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_version;
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_distribution;
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_machine;
    REFRESH MATERIALIZED VIEW CONCURRENTLY results_version_details;
END;
$$ LANGUAGE plpgsql;