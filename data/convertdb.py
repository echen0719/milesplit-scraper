import os
import psutil
import duckdb

athletesSource = "raw/athletes/"
athletesParquet = "parquet/athletes"

if not os.path.exists(athletesSource):
    os.makedirs(athletesSource)
if not os.path.exists(athletesParquet):
    os.makedirs(athletesParquet)

threadsCount = max(1, (os.cpu_count() or 2) - 1)
memoryAvaliable = psutil.virtual_memory().available // (1024 ** 3)
memoryLimit = max(1, memoryAvaliable - 4)

def createDB(source, parquet):
    dbName = "milesplit-{}.duckdb".format(source.split("/")[1])
    con = duckdb.connect(dbName)

    con.execute("SET threads = {}".format(threadsCount))
    con.execute("SET memory_limit = '{}GB'".format(memoryLimit)) # save 4GB

    print("Convert the JSON to Parquets")

    # reduce on the number of lines in this SQL
    con.execute("""
        COPY (
            SELECT
                _embedded.athlete.id AS athlete_id,
                _embedded.athlete.firstName AS first_name,
                _embedded.athlete.lastName AS last_name,
                _embedded.athlete.gender as gender,
                _embedded.athlete.schoolId as school_id,
                _embedded.athlete.gradYear AS grad_year,
                _embedded.athlete.collegeYear AS college_year,
                _embedded.athlete.collegeId AS college_id,
                _embedded.athlete.city AS city,
                _embedded.athlete.state AS state,
                _embedded.athlete.teamId AS team_id,
                race.id AS event_id,
                race.meetId AS meet_id,
                race.meetName AS meet_name,
                race.eventCode AS event_code,
                race.round AS event_round,
                race.season AS event_season,
                race.mark AS event_mark
            FROM (
                SELECT
                    _embedded,
                    unnest(data) AS race
                FROM read_json_auto('{}/*.json', ignore_errors=true)
            )
        ) TO '{}/data.parquet' (FORMAT PARQUET, COMPRESSION ZSTD, PER_THREAD_OUTPUT true)
    """.format(source, parquet))

    print("Converting the Parquets to a DuckDB")

    con.execute("""
        CREATE TABLE athlete_events AS
        SELECT * FROM read_parquet('{}/data*.parquet')
    """.format(parquet))

    print("Created a database at: {}".format(dbName))
    con.close()

createDB(athletesSource, athletesParquet)