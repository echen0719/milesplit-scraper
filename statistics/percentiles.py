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

runEvents = ["5000m", "1600m"] # "100m", "200m", "400m", "800m", "3200m", "300H", "3Mile", "100H", "2Mile", "110H", "3000m", "55m", "1500m", "60m", "300m", "Mile"]

# all these in ms
plausibleTimes = {
    "5000m": (755.36 * 1000, 18000 * 1000), # WR 5K, 5 hours
    "1600m": (220.5 * 1000, 5400 * 1000) # WR ~1600m, 90 minutes
    # add next times
}

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
    results = con.execute(query, [runEvent]).fetchall()

    matched = 0
    checked = 0

    for mark, units in results:
        expectedUnits = parseTime(mark) * 1000

        if expectedUnits - tolerance <= float(units) <= expectedUnits + tolerance:
            matched += 1
        checked += 1

    print("{}: {:.2f}% meaning {} \"invalid times\" out of {}".format(runEvent, matched / checked * 100, checked - matched, checked))

# units are measured in milliseconds for running events
def analyze(gender, results, runEvent):
    plausibleMinTime, plausibleMaxTime = plausibleTimes[runEvent]
    validResults = []
    excludedResults = []

    for athleteID, units in results:
        mseconds = float(units)

        if mseconds > 0 and plausibleMinTime <= mseconds <= plausibleMaxTime:
            validResults.append((athleteID, mseconds))
        else:
            excludedResults.append((athleteID, mseconds))

    # lamba notation
    fastest10 = heapq.nsmallest(10, validResults, key=lambda x: x[1])
    slowest10 = heapq.nlargest(10, validResults, key=lambda x: x[1])

    validTimes = np.array([result[1] / 1000 for result in validResults])
    q1, q3 = np.percentile(validTimes, [25, 75])
    mean = np.mean(validTimes)
    median = np.median(validTimes)
    std = np.std(validTimes)
    normal = NormalDist(mu=float(mean), sigma=float(std))

    print("\nTotal results for the {} in the {}: {}".format(gender, runEvent, len(validTimes)))
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

for runEvent in runEvents:
    query = "SELECT {}, {} FROM {} WHERE {} = ? AND {} = ?".format(columns["ATHLETE_ID"], columns["EVENT_UNITS"], tableName, columns["GENDER"], columns["EVENT_CODE"])
    boysRaceResults = con.execute(query, ["M", runEvent]).fetchall()
    girlsRaceResults = con.execute(query, ["F", runEvent]).fetchall()

    # checkUnits()
    # 1600m: 100.00% meaning 106 "invalid times" out of 9326213
    # 5K: 99.98% meaning 4952 "invalid times" out of 26899014

    print("\n=======Event: {}=======".format(runEvent))

    print("\n--------------Boys--------------")
    analyze("boys", boysRaceResults, runEvent)
    print("\n--------------Girls--------------")
    analyze("girls", girlsRaceResults, runEvent)