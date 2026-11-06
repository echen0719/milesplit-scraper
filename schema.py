import json
import os

def loadSchema():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json")
    with open(path, "r") as file:
        return json.load(file)

schema = loadSchema()
tableName = schema["table_name"]
columns = schema["columns"]