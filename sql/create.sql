-- a function producing simple JSON compatible ISO timestamp
CREATE OR REPLACE FUNCTION isodate(timestamp) RETURNS text AS $$
SELECT to_char($1, 'YYYY-MM-DD"T"HH24:MI:SS')
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
    dist_version    TEXT NOT NULL,
    dist_date	    TIMESTAMP NOT NULL,

    -- replace by proper enum
    dist_status     TEXT NOT NULL

);

-- machines doing the tests
CREATE TABLE animals (

    id              SERIAL PRIMARY KEY,

    animal_name     TEXT NOT NULL UNIQUE,
    animal_secret   TEXT NOT NULL DEFAULT random_string(32),

    -- description, contact e-mail etc.
    animal_desc     TEXT,
    animal_email    TEXT NOT NULL,

    -- all animals need to be approved first
    animal_approved BOOLEAN NOT NULL DEFAULT false,

    -- false => deleted, disabled animals
    animal_active   BOOLEAN NOT NULL DEFAULT true

);

CREATE TABLE results (

    id              SERIAL PRIMARY KEY,

    -- public ID of the result (random UUID)
    result_uuid     TEXT NOT NULL UNIQUE,

    animal_id       INT NOT NULL REFERENCES animals(id),
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
    load_result     BOOLEAN,
    install_result  BOOLEAN,
    check_result    BOOLEAN,

    -- log from each phase (if available), and a diff from the pg_regress check
    log_load        TEXT,
    log_install     TEXT,
    log_check       TEXT,
    check_diff      TEXT

);
