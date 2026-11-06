import os
import sys
import duckdb
import pandas as pd # to display the sample

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import tableName

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)

relish = con.query("SELECT * FROM {}".format(tableName))
print("Shape of the database:", relish.shape, "\n") # ~190,000,000 x 18

columns = con.execute("DESCRIBE {}".format(tableName)).fetchall()
for column in columns:
    colName = column[0]
    colType = column[1]

    distinctCount = con.execute("SELECT COUNT(DISTINCT {}) FROM {}".format(colName, tableName)).fetchone()[0]
    print("Column: {} \t|\t Type: {} \t|\t Number of distinct values: {}".format(colName, colType, distinctCount))

# randomly pick 100 times to look at
sample = con.execute("SELECT * FROM {} ORDER BY RANDOM() LIMIT 100".format(tableName)).fetchdf()
print("\n", sample.to_string(index=False))

# Shape of the database: (189559933, 18)
#
# Column: athlete_id      |        Type: VARCHAR  |        Number of distinct values: 14892438
# Column: first_name      |        Type: VARCHAR  |        Number of distinct values: 676869
# Column: last_name       |        Type: VARCHAR  |        Number of distinct values: 1228589
# Column: gender  |        Type: VARCHAR  |        Number of distinct values: 13
# Column: school_id       |        Type: VARCHAR  |        Number of distinct values: 57212
# Column: grad_year       |        Type: VARCHAR  |        Number of distinct values: 329
# Column: college_year    |        Type: VARCHAR  |        Number of distinct values: 46
# Column: college_id      |        Type: VARCHAR  |        Number of distinct values: 6006
# Column: city    |        Type: VARCHAR  |        Number of distinct values: 15686
# Column: state   |        Type: VARCHAR  |        Number of distinct values: 233
# Column: team_id         |        Type: VARCHAR  |        Number of distinct values: 57116
# Column: event_id        |        Type: BIGINT   |        Number of distinct values: 189368082
# Column: meet_id         |        Type: VARCHAR  |        Number of distinct values: 520644
# Column: meet_name       |        Type: VARCHAR  |        Number of distinct values: 280094
# Column: event_code      |        Type: VARCHAR  |        Number of distinct values: 257
# Column: event_round     |        Type: VARCHAR  |        Number of distinct values: 6
# Column: event_season    |        Type: VARCHAR  |        Number of distinct values: 4
# Column: event_mark      |        Type: VARCHAR  |        Number of distinct values: 595152

# not adding the sample