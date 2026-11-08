import os
import sys
import duckdb
import numpy as np
from statistics import NormalDist
import heapq

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

def checkUnits(tolerance=200): # 0.2 second tolerance
    query = "SELECT {}, {} FROM {} WHERE {} = ?".format(columns["EVENT_MARK"], columns["EVENT_UNITS"], tableName, columns["EVENT_CODE"])
    results = con.execute(query, ["5000m"]).fetchall()

    matched = 0
    checked = 0

    for mark, units in results:
        expectedUnits = parseTime(mark) * 1000

        if expectedUnits - tolerance <= float(units) <= expectedUnits + tolerance:
            matched += 1
        checked += 1

    print("Units to marks matching percentage for the 5K: {:.2f}% meaning {} \"invalid times\" out of {}".format(matched / checked * 100, checked - matched, checked))

# units are measured in milliseconds for running events
def analyze(gender, results):
    validResults = []
    excludedResults = []

    plausibleMinTime = 755.36 * 1000.0 # WR 5K
    plausibleMaxTime = 18000 * 1000.0 # 5 hours

    for athleteID, units in results:
        mseconds = float(units)
        if mseconds > 0 and plausibleMinTime <= mseconds <= plausibleMaxTime:
            validResults.append((athleteID, mseconds))
        else:
            excludedResults.append((athleteID, mseconds))

    # lamba notation
    fastest10 = heapq.nsmallest(10, validResults, key=lambda x: x[1])
    slowest10 = heapq.nlargest(10, validResults, key=lambda x: x[1])

    plausibleTimes = np.array([result[1] / 1000 for result in validResults])
    q1, q3 = np.percentile(plausibleTimes, [25, 75])
    mean = np.mean(plausibleTimes)
    median = np.median(plausibleTimes)
    std = np.std(plausibleTimes)
    normal = NormalDist(mu=float(mean), sigma=float(std))

    print("\nTotal results for the {}:".format(gender), len(plausibleTimes))
    print("Excluded as outliers:", len(excludedResults))

    print("\nFastest 10 athletes: ")
    for i, (athleteID, mseconds) in enumerate(fastest10, 1):
        print("{}. Athlete {}: {:.2f} seconds".format(i, athleteID, mseconds / 1000))

    print("\nSlowest 10 athletes: ")
    for i, (athleteID, mseconds) in enumerate(slowest10, 1):
        print("{}. Athlete {}: {:.2f} seconds".format(i, athleteID, mseconds / 1000))

    print("\nQ1: {:.2f} seconds".format(q1))
    print("Median: {:.2f} seconds".format(median))
    print("Mean: {:.2f} seconds".format(mean))
    print("Standard deviation: {:.2f} seconds".format(std))
    print("Q3: {:.2f} seconds".format(q3))

query = "SELECT {}, {} FROM {} WHERE {} = ? AND {} = ?".format(columns["ATHLETE_ID"], columns["EVENT_UNITS"], tableName, columns["GENDER"], columns["EVENT_CODE"])
male5Kresults = con.execute(query, ["M", "5000m"]).fetchall()
female5Kresults = con.execute(query, ["F", "5000m"]).fetchall()

# checkUnits() # Units to marks matching percentage for the 5K: 99.98% meaning 4952 "invalid times" out of 26899014
analyze("boys", male5Kresults)
print("\n========================")
analyze("girls", female5Kresults)