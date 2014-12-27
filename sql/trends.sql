-- summary of results per month of version release
CREATE MATERIALIZED VIEW stats_monthly AS
SELECT
    release_month,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        lr.pg_version AS major_version,
        date_trunc('month', version_date)::date AS release_month,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
) foo GROUP BY 1 ORDER BY 1;

CREATE UNIQUE INDEX stats_monthly_idx ON stats_monthly (release_month);

-- summary of results per month of version release and major version
CREATE MATERIALIZED VIEW stats_monthly_versions AS
SELECT
    release_month,
    major_version,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        lr.pg_version AS major_version,
        date_trunc('month', version_date)::date AS release_month,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
) foo GROUP BY 1,2 ORDER BY 1, 2;

CREATE UNIQUE INDEX stats_monthly_versions_idx ON stats_monthly_versions (release_month, major_version);

-- summary of results per month of version release and version status
CREATE MATERIALIZED VIEW stats_monthly_version_status AS
SELECT
    release_month,
    version_status,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        version_status,
        date_trunc('month', version_date)::date AS release_month,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
) foo GROUP BY 1, 2 ORDER BY 1, 2;

CREATE UNIQUE INDEX stats_monthly_version_status_idx ON stats_monthly_version_status (release_month, version_status);

-- current status - for each distribution, take only the very last version
-- for each status (and then last result from each machine)
CREATE MATERIALIZED VIEW stats_current AS
SELECT
    1 AS id,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
                                 JOIN version_last lv ON (v.id = lv.version_id) -- last version for each status
) foo;

CREATE UNIQUE INDEX stats_current_idx ON stats_current (id);

CREATE MATERIALIZED VIEW stats_current_versions AS
SELECT
    major_version,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        lr.pg_version AS major_version,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
                                 JOIN version_last lv ON (v.id = lv.version_id) -- last version for each status
) foo GROUP BY 1 ORDER BY 1;

CREATE UNIQUE INDEX stats_current_versions_idx ON stats_current_versions (major_version);

-- current stats
CREATE MATERIALIZED VIEW stats_current_version_status AS
SELECT
    version_status,
    COUNT(*) AS total_count,
    COUNT(DISTINCT id) AS version_count,
    COUNT(CASE WHEN result = 'install' THEN 1 END) AS install_errors,
    COUNT(CASE WHEN result = 'load' THEN 1 END)    AS load_errors,
    COUNT(CASE WHEN result = 'check' THEN 1 END)   AS check_errors,
    COUNT(CASE WHEN result = 'check missing' THEN 1 END) as check_missing,
    COUNT(CASE WHEN result = 'ok' THEN 1 END) AS ok_count
FROM (
    SELECT
        v.id,
        v.version_status,
        (CASE
            WHEN install_result = 'error' THEN 'install'
            WHEN load_result = 'error' THEN 'load'
            WHEN check_result = 'error' THEN 'check'
            WHEN check_result = 'missing' THEN 'check missing'
            ELSE 'ok' END) AS result
    FROM distribution_versions v JOIN results r ON (r.dist_version_id = v.id)
                                 JOIN results_last lr ON (r.id = lr.result_id)	-- last result from each machine (for major version)
                                 JOIN version_last lv ON (v.id = lv.version_id) -- last version for each status
) foo GROUP BY 1 ORDER BY 1;

CREATE UNIQUE INDEX stats_current_version_status_idx ON stats_current_version_status (version_status);

CREATE MATERIALIZED VIEW stats_errors AS
SELECT
    error_phase,
    description,
    count(*) AS count
FROM
    error_analysis ea JOIN results_last lr ON (lr.result_id = ea.result_id)
GROUP BY 1, 2;

CREATE UNIQUE INDEX stats_errors_idx ON stats_errors (error_phase, description);

CREATE MATERIALIZED VIEW stats_errors_by_status AS
SELECT
    version_status,
    error_phase,
    description,
    count(*) AS count
FROM
    error_analysis ea JOIN results_last lr ON (lr.result_id = ea.result_id)
                      JOIN results r ON (r.id = ea.result_id)
                      JOIN version_last lv ON (r.dist_version_id = lv.version_id)
GROUP BY 1, 2, 3;

CREATE UNIQUE INDEX stats_errors_by_status_idx ON stats_errors_by_status (version_status, error_phase, description);

CREATE OR REPLACE FUNCTION refresh_stats() RETURNS void AS $$
BEGIN

    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_current;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_current_versions;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_current_version_status;

    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_monthly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_monthly_versions;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_monthly_version_status;

    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_errors;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_errors_by_status;

END;
$$ LANGUAGE plpgsql;
