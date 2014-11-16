CREATE TABLE error_analysis (

    id              SERIAL PRIMARY KEY,

    result_id       INT NOT NULL REFERENCES results(id),

    -- description, contact e-mail etc.
    error_phase     TEXT,
    description     TEXT,

    CONSTRAINT valid_phase CHECK (error_phase IN ('install', 'load', 'check'))

);


CREATE OR REPLACE FUNCTION analyze_install_errors() RETURNS void AS $$
DECLARE
    v_row RECORD;
BEGIN

    FOR v_row IN (SELECT id, log_install FROM results WHERE install_result = 'error') LOOP

        DELETE FROM error_analysis WHERE result_id = v_row.id;

        IF (v_row.log_install LIKE '%Makefile.global%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'mising Makefile.global');

        ELSIF (v_row.log_install LIKE '%no Makefile found in the extension root%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'mising Makefile in extension root');

        ELSIF (v_row.log_install LIKE '%will not overwrite just-created%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'will not overwrite just-created file');

        ELSIF (v_row.log_install LIKE '%missing destination file operand%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'missing destination file operand');

        ELSIF (v_row.log_install LIKE '%no input file specified%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'no input file specified');

        ELSIF (v_row.log_install LIKE '%No such file or directory%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'no such file or directory');

        ELSIF (v_row.log_install LIKE '%No rule to make target%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'missing makefile target');

        ELSIF (v_row.log_install LIKE '%Command not found%')
        OR (v_row.log_install LIKE '%command not found%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'command not found');

        ELSIF (v_row.log_install LIKE '%error: %: No such file or directory%')
        OR (v_row.log_install LIKE '%catastrophic error: cannot open source file%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'no such file or directory');

        ELSIF (v_row.log_install LIKE '%error: identifier "%" is undefined%')
        OR (v_row.log_install LIKE '%error: ''%'' undeclared%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'undeclared identifier');

        ELSIF (v_row.log_install LIKE '%error: ''%'' has no member named ''%''%')
        OR (v_row.log_install LIKE '%error: struct "%" has no field "%"%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'struct member missing');

        ELSIF (v_row.log_install LIKE '%error: incompatible types when assigning to type%')
        OR (v_row.log_install LIKE '%error: a value of type "%" cannot be assigned to an entity of type%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'incompatible types in assignment');

        ELSIF (v_row.log_install LIKE '%too many arguments in function call%')
        OR (v_row.log_install LIKE '%error: too many arguments to function%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'too many arguments in a function call');

        ELSIF (v_row.log_install LIKE '%too few arguments in function call%')
        OR (v_row.log_install LIKE '%error: too few arguments to function%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'too few arguments in a function call');

        ELSIF (v_row.log_install LIKE '%configure: error: % is not installed, but is required by debversion%') T

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'configure missing library');

        ELSIF (v_row.log_install LIKE '%cannot create regular file %: Permission denied%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'permission denied');

        ELSIF (v_row.log_install LIKE '%config/install-sh: % does not exist.%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'installed file missing');

        ELSIF (v_row.log_install LIKE '%error: invalid type argument%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'invalid type argument');

        ELSIF (v_row.log_install LIKE '%undefined reference to%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'undefined reference when linking');

        ELSIF (v_row.log_install LIKE '%error: pointer to incomplete class type is not allowed%')
        OR (v_row.log_install LIKE '%error: dereferencing pointer to incomplete type%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'dereferencing pointer to incomplete type');

        ELSIF (v_row.log_install LIKE '%You need to run the ''configure'' program first. See the file%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'configure not executed');

        ELSIF (v_row.log_install LIKE '%error: declaration is incompatible%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'incompatible declaration');

        ELSIF (v_row.log_install LIKE '%requires PostgreSQL % or above%')
        OR (v_row.log_install LIKE '%error: #error directive: Wrong Postgresql version.%')
        OR (v_row.log_install LIKE '%error: #error Wrong Postgresql version%')
        OR (v_row.log_install LIKE '%#error wrong Postgresql version%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'unsupported PostgreSQL version');

        ELSIF (v_row.log_install LIKE '%#error Must compile with c99 or define%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'c99 compiler required');

        ELSIF (v_row.log_install LIKE '%unexpected error: OSError - [Errno 17] File exists%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'unexpected error - file exists');

        ELSIF (v_row.log_install LIKE '%ld: cannot find -lpython2.7%')
        OR (v_row.log_install LIKE '%Found Python 2.6, but 2.7 is required.%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'incompatible python version');

        ELSIF (v_row.log_install LIKE '%error: expected an expression%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'expected an expression');

        ELSIF (v_row.log_install LIKE '%error: expression must have pointer type%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'expression must have pointer type');

        ELSIF (v_row.log_install LIKE '%missing separator.  Stop.%') THEN

            INSERT INTO error_analysis(result_id, error_phase, description)
            VALUES (v_row.id, 'install', 'missing separator');

        END IF;

    END LOOP;

END;
$$ LANGUAGE plpgsql;
