import os
import psutil
import duckdb

source = "raw/"
output = "parquet/"
os.mkdir(output, exist_ok=True)

threadsCount = max(1, (os.cpu_count() or 2) - 1)
memoryAvaliable = psutil.virtual_memory().available / (1024 ** 3))
memoryLimit = max(1, memoryAvaliable - 4)

con = duckdb.connect()
con.execute("SET thread = {}".format(threadsCount))
con.execute("SET memory_limit = {}GB".format(memoryLimit)) # save 4GB

# batching setup
batchSize = 100000
batch = []

