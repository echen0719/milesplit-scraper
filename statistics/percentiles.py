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
meetExclusions = ["631386", "631387", "632242"] # malformed races

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

def getExclusionSQL(column):
    if not meetExclusions:
        return ""

    placeholders = ", ".join("?" * len(meetExclusions)) # --> produces , ?, ?, ?
    return " AND {} NOT IN ({})".format(column, placeholders)

exclusionSQL = getExclusionSQL(columns["MEET_ID"])

def parseTime(time):
    if time is None: return None
    mark = time.strip().strip('"')

    if ":" in mark:
        parts = mark.split(":")

        if len(parts) == 2: # mm:ss.ff
            minutes, seconds = parts
            minutes = int(minutes)
            seconds = float(seconds)

            if minutes < 0 or not 0 <= seconds <= 60:
                return None
            return minutes * 60 + seconds

        elif len(parts) == 3: # hh:mm:ss.ff
            hours, minutes, seconds = parts
            hours = int(hours)
            minutes = int(minutes)
            seconds = float(seconds)

            if hours < 0 or minutes < 0 or not 0 <= minutes < 60 or not 0 <= seconds <= 60:
                return None
            return hours * 3600 + minutes * 60 + seconds

    elif mark.count(".") == 1:
        seconds = float(mark)

        if seconds < 0:
            return None
        return seconds

    else:
        return None # that's for null values

def checkUnits(results, runEvent, tolerance=50): # 0.05 second tolerance
    matched = 0
    checked = 0
    invalids = []

    for athleteID, _, mark, units, meetID in results:
        parsedTime = parseTime(mark)
        if not parsedTime is None:
            expectedUnits = parsedTime * 1000

            if expectedUnits - tolerance <= float(units) <= expectedUnits + tolerance:
                matched += 1
            else:
                invalids.append((athleteID, mark, units, meetID))
        else:
            invalids.append((athleteID, mark, units, meetID))
        checked += 1

    # print("{}: {:.2f}% meaning {} \"invalid times\" out of {}".format(runEvent, matched / checked * 100, checked - matched, checked))
    return invalids

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

def main():
    for runEvent in runEvents:
        query = "SELECT {}, {},  {}, {}, {} FROM {} WHERE {} = ? {}".format(
            columns["ATHLETE_ID"],
            columns["GENDER"],
            columns["EVENT_MARK"],
            columns["EVENT_UNITS"],
            columns["MEET_ID"],
            tableName,
            columns["EVENT_CODE"],
            exclusionSQL
        ) # too long for one-liner

        results = con.execute(query, [runEvent] + meetExclusions).fetchall()
        invalidPerformances = set(checkUnits(results, runEvent))

        # 5000m: 100.00% meaning 949 "invalid times" out of 26884147
        # 1600m: 100.00% meaning 21 "invalid times" out of 9326212
        boysRaceResults = []
        girlsRaceResults = []

        for athleteID, gender, mark, units, meetID in results:
            if (athleteID, mark, units, meetID) in invalidPerformances:
                continue

            if gender == "M":
                boysRaceResults.append((athleteID, units))
            elif gender == "F":
                girlsRaceResults.append((athleteID, units))

        print("\n=======Event: {}=======".format(runEvent))

        print("\n--------------Boys--------------")
        analyzeTotal("boys", boysRaceResults, runEvent)

        print("\n--------------Girls--------------")
        analyzeTotal("girls", girlsRaceResults, runEvent)

if __name__ == "__main__":
    main()