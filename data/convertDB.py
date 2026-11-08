import os
import sys
import psutil
import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import columns, tableName

athletesSource = "raw/athletes"
athletesParquet = "parquet/athletes"

if not os.path.exists(athletesSource):
    os.makedirs(athletesSource)
if not os.path.exists(athletesParquet):
    os.makedirs(athletesParquet)

threadsCount = max(1, (os.cpu_count() or 2) - 1)
memoryAvaliable = psutil.virtual_memory().available // (1024 ** 3)
memoryLimit = max(1, memoryAvaliable - 4)

def createDB(source, parquet, batchSize):
    dbName = "milesplit-{}.duckdb".format(source.split("/")[1])
    con = duckdb.connect(dbName)
    jsonFiles = [os.path.join(source, json) for json in os.listdir(source)]

    con.execute("SET threads = {}".format(threadsCount))
    con.execute("SET memory_limit = '{}GB'".format(memoryLimit)) # save 4GB

    print("Convert the JSON to Parquets")

    for i in range(0, len(jsonFiles), batchSize):
        start = i
        end = min(i + batchSize, len(jsonFiles))

        print("Processing batch from {} to {}".format(start, end))
        batch = jsonFiles[start : end]

        # reduce on the number of lines in this SQL
        con.execute("""
            COPY (
                SELECT
                    _embedded.athlete.id AS {ATHLETE_ID},
                    _embedded.athlete.firstName AS {FIRST_NAME},
                    _embedded.athlete.lastName AS {LAST_NAME},
                    _embedded.athlete.gender AS {GENDER},
                    _embedded.athlete.schoolId AS {SCHOOL_ID},
                    _embedded.athlete.gradYear AS {GRAD_YEAR},
                    _embedded.athlete.collegeYear AS {COLLEGE_YEAR},
                    _embedded.athlete.collegeId AS {COLLEGE_ID},
                    _embedded.athlete.birthYear AS {BIRTH_YEAR},
                    _embedded.athlete.city AS {CITY},
                    _embedded.athlete.state AS {STATE},
                    _embedded.athlete.country AS {COUNTRY},
                    _embedded.athlete.teamId AS {TEAM_ID},
                    race.id AS {EVENT_ID},
                    race.meetId AS {MEET_ID},
                    race.units AS {EVENT_UNITS},
                    race.meetName AS {MEET_NAME},
                    race.eventCode AS {EVENT_CODE},
                    race.round AS {EVENT_ROUND},
                    race.season AS {EVENT_SEASON},
                    race.mark AS {EVENT_MARK}
                FROM (
                    SELECT
                        _embedded,
                        unnest(data) AS race
                    FROM read_json_auto(?, ignore_errors=true)
                )
            ) TO '{}/data_{}.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
        """.format(parquet, i, **columns), [batch]) # execute on batched

    print("Converting the Parquets to a DuckDB")

    con.execute("""
        CREATE TABLE {} AS
        SELECT * FROM read_parquet('{}/data*.parquet')
    """.format(tableName, parquet))

    print("Created a database at: {}".format(dbName))
    con.close()

createDB(athletesSource, athletesParquet, 500000)