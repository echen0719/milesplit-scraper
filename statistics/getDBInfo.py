import sys
import duckdb
import pandas as pd # to display the sample

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)
tableName = "athlete_events"

relish = con.query("SELECT * FROM {}".format(tableName))
print("Shape of the database:", relish.shape, "\n") # ~190,000,000 x 18

columns = con.execute("DESCRIBE {}".format(tableName)).fetchall()
for column in columns:
    print("Column: {} \t| \tType: {}".format(column[0], column[1]))

# randomly pick 100 times to look at
sample = con.execute("SELECT * FROM {} ORDER BY RANDOM() LIMIT 100".format(tableName)).fetchdf()
print("\n", sample.to_string(index=False))