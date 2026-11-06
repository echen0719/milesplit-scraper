import os
import sys
import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import columns, tableName

if len(sys.argv) < 2:
    print("Usage: python {} <database.duckdb>".format(sys.argv[0]))
    exit()

dbFile = sys.argv[1]
con = duckdb.connect(dbFile)

# gets the element with top 5 frequency
def getPopular(columnName, distinct=False):
    result = con.execute("""
        SELECT {}, COUNT({}) AS frequency
        FROM {} GROUP BY {}
        ORDER BY frequency DESC LIMIT 5;
    """.format(columnName, "DISTINCT {}".format(columns["ATHLETE_ID"]) if distinct else "*", tableName, columnName))

    return result.fetchall()

print("First name:", getPopular(columns["FIRST_NAME"], distinct=True))
print("Last name:", getPopular(columns["LAST_NAME"], distinct=True))
print("Meet:", getPopular(columns["MEET_NAME"]))
print("Event:", getPopular(columns["EVENT_CODE"]))
print("Time/Mark:", getPopular(columns["EVENT_MARK"]))
print("Team ID:", getPopular(columns["TEAM_ID"], distinct=True))
print("City:", getPopular(columns["CITY"], distinct=True))
print("State:", getPopular(columns["STATE"], distinct=True))

# First name: [('Michael', 83992), ('Jacob', 83754), ('Alex', 83111), ('Ryan', 77204), ('Andrew', 75653)]
# Last name: [('Smith', 126318), ('Johnson', 110392), ('Williams', 96373), ('Jones', 80456), ('Brown', 79929)]
# Meet: [('AAU Junior Olympic Games', 147045), ('Mt SAC Invitational', 97135), ('Woodbridge Cross Country Classic', 92654), ('NJSIAA Group Championships', 86153), ('Bulldog Invitational', 75612)]
# Event: [('5000m', 26899014), ('100m', 16483226), ('200m', 15360708), ('S', 12747532), ('400m', 11527560)]
# Time/Mark: [('4-6', 396601), ('5-0', 365142), ('4-8', 356153), ('5-6', 334513), ('4-4', 331131)]
# Team ID: [(None, 370060), ('31976', 18509), ('39804', 12972), ('30612', 10103), ('30638', 9157)]
# City: [('', 814427), ('Houston', 75388), ('Louisville', 74180), ('Chicago', 66718), ('San Antonio', 53340)]
# State: [('TX', 1305686), ('CA', 1207468), ('FL', 655280), ('OH', 650043), ('NY', 609828)]