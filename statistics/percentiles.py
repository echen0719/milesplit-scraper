import os
import sys
import duckdb
import numpy as np
import heapq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import columns, tableName

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)

runEvents = ["5000m", "1600m"] # "100m", "200m", "400m", "800m", "3200m", "Mile" in future

# all these in ms
plausibleTimes = {
    "5000m": {
        "M": {"min": 755.36 * 1000, "max": 18000 * 1000}, # WR 5K, 5 hours
        "F": {"min": 838.06 * 1000, "max": 18000 * 1000} # WR 5K, 5 hours
    },
    "1600m": {
        "M": {"min": 221 * 1000, "max": 3600 * 1000}, # WR ~1600m, 1 hour
        "F": {"min": 244 * 1000, "max": 3600 * 1000}
    }
}

def parseTime(time):
    if time is None: return None
    parts = time.strip().strip('"').split(":")

    if len(parts) == 1: # ss.ff
        return float(parts[0])
    if len(parts) == 2: # mm:ss.ff
        minutes, seconds = parts
        return (int(minutes) * 60) + float(seconds)
    elif len(parts) == 3: # hh:mm:ss.ff
        hours, minutes, seconds = parts
        return (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
    else:
        return None # that's for null values

def checkUnits(tolerance=50): # 0.05 second tolerance
    query = "SELECT {}, {}, {} FROM {} WHERE {} = ?".format(columns["ATHLETE_ID"], columns["EVENT_MARK"], columns["EVENT_UNITS"], tableName, columns["EVENT_CODE"])
    results = con.execute(query, [runEvent]).fetchall()

    matched = 0
    checked = 0

    for athleteID, mark, units in results:
        parsedTime = parseTime(mark)
        expectedUnits = parseTime(mark) * 1000

        if expectedUnits - tolerance <= float(units) <= expectedUnits + tolerance:
            matched += 1
        checked += 1

    print("{}: {:.2f}% meaning {} \"implausible times\" out of {}".format(runEvent, matched / checked * 100, checked - matched, checked))

# units are measured in milliseconds for running events
def analyzeTotal(gender, results, runEvent):
    plausibleMinTime = plausibleTimes[runEvent]["M" if gender == "boys" else "F"]["min"]
    plausibleMaxTime = plausibleTimes[runEvent]["M" if gender == "boys" else "F"]["max"]

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
    percentileNames = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    percentiles = np.percentile(validTimes, percentileNames)
    mean = np.mean(validTimes)
    median = np.median(validTimes)
    std = np.std(validTimes)

    print("\nTotal results for the {} in the {}: {}".format(gender, runEvent, len(validTimes)))
    print("Excluded as outliers:", len(excludedResults))

    print("\nFastest 10 performances: ")
    for i, (athleteID, mseconds) in enumerate(fastest10, 1):
        print("{}. Athlete {}: {:.2f} seconds".format(i, athleteID, mseconds / 1000))

    print("\nSlowest 10 performances: ")
    for i, (athleteID, mseconds) in enumerate(slowest10, 1):
        print("{}. Athlete {}: {:.2f} seconds".format(i, athleteID, mseconds / 1000))

    print("\nPercentiles:")

    for name, value in zip(percentileNames, percentiles):
        print("P{}: {:.2f} seconds".format(name, value))

    print("\nMedian: {:.2f} seconds".format(median))
    print("Mean: {:.2f} seconds".format(mean))
    print("Standard deviation: {:.2f} seconds".format(std))

for runEvent in runEvents:
    query = "SELECT {}, {} FROM {} WHERE {} = ? AND {} = ?".format(columns["ATHLETE_ID"], columns["EVENT_UNITS"], tableName, columns["GENDER"], columns["EVENT_CODE"])
    boysRaceResults = con.execute(query, ["M", runEvent]).fetchall()
    girlsRaceResults = con.execute(query, ["F", runEvent]).fetchall()

    # checkUnits()
    # 1600m: 100.00% meaning 21 "implausible times" out of 9326213
    # 5000m: 99.98% meaning 4798 "implausible times" out of 26899014

    print("\n=======Event: {}=======".format(runEvent))

    print("\n--------------Boys--------------")
    analyzeTotal("boys", boysRaceResults, runEvent)
    print("\n--------------Girls--------------")
    analyzeTotal("girls", girlsRaceResults, runEvent)