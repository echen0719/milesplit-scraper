import os
import sys
import duckdb
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
    parts = time.strip().strip('"').split(":")

    if len(parts) == 2: # mm:ss.ff
        minutes, seconds = parts
        return (int(minutes) * 60) + float(seconds)
    elif len(parts) == 3: # hh:mm:ss.ff
        hours, minutes, seconds = parts
        return (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
    else:
        return 0 # that's for null values

def analyze(gender, results):
    validResults = []
    excludedResults = []

    plausibleMinTime = 755.36 # WR 5K
    plausibleMaxTime = 7200 # 2 hours

    for athleteID, mark in results:
        seconds = parseTime(mark)
        if seconds > 0 and plausibleMinTime <= seconds <= plausibleMaxTime:
            validResults.append((athleteID, mark, seconds))
        else:
            excludedResults.append((athleteID, mark, seconds))

    # lamba notation
    fastest = min(validResults, key=lambda x: x[1])
    slowest = max(validResults, key=lambda x: x[1])

    plausibleTimes = np.array([result[2] for result in validResults])
    q1, q3 = np.percentile(plausibleTimes, [25, 75])
    mean = np.mean(plausibleTimes)
    median = np.median(plausibleTimes)
    std = np.std(plausibleTimes)
    normal = NormalDist(mu=float(mean), sigma=float(std))

    print("\nTotal results for the {}:".format(gender), len(plausibleTimes))
    print("Excluded as outliers:", len(excludedResults))

    print("\nFastest athlete ({}): {} or {:.2f} seconds".format(fastest[0], fastest[1], fastest[2]))
    print("Slowest athlete ({}): {} or {:.2f} seconds".format(slowest[0], slowest[1], slowest[2]))

    print("\nQ1: {:.2f} seconds".format(q1))
    print("Median: {:.2f} seconds".format(median))
    print("Mean: {:.2f} seconds".format(mean))
    print("Standard deviation: {:.2f} seconds".format(std))
    print("Q3: {:.2f} seconds".format(q3))

query = "SELECT {}, {} FROM {} WHERE {} = ? AND {} = ?".format(columns["ATHLETE_ID"], columns["EVENT_MARK"], tableName, columns["GENDER"], columns["EVENT_CODE"])
male5Kresults = con.execute(query, ["M", "5000m"]).fetchall()
female5Kresults = con.execute(query, ["F", "5000m"]).fetchall()

analyze("boys", male5Kresults)
analyze("girls", female5Kresults)