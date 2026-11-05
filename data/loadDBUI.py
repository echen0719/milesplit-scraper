import sys
import duckdb

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)

print(con.sql("INSTALL ui FROM core;"))
print(con.sql("LOAD ui;"))
print(con.sql("CALL start_ui();"))

input("\nPress enter to exit...")