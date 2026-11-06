import os
import sys
import duckdb
from datetime import datetime # no regex on time :D
import numpy as np
from statistics import NormalDist

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import columns, tableName

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)

def parseTime(time):
    dt = datetime.strptime(time, "%M:%S.%f")
    return (dt.minute * 60) + dt.second + (dt.microsecond / 1_000_000)

query = "SELECT {} FROM {} WHERE {} = ? AND {} = ? LIMIT 10".format(columns["EVENT_MARK"], tableName, columns["GENDER"], columns["EVENT_CODE"])
male5Kresults = con.execute(query, ["M", "5000m"]).fetchall()
female5Kresults = con.execute(query, ["F", "5000m"]).fetchall()