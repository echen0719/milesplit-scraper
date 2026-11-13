import asyncio
import aiohttp
import aiofiles # for dumps
import json
import sys
import os

import random
import string

# all TOR
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

torProxy = "socks5://127.0.0.1:9050"
numWorkers = 50

class IDCounter:
    def __init__(self, start, total):
        self.start = start
        self.total = total
        self.current = start
        self.lock = asyncio.Lock() # say no to fighting!

    async def nextID(self):
        async with self.lock:
            if self.current >= self.total:
                return
            currentID = self.current
            self.current += 1
            return currentID

async def getMeet(session, meetID, workerID, fileOutput, retries):
    statsLink = "https://www.milesplit.com/api/v1/meets/{}/stats".format(meetID)

    try:
        async with session.get(statsLink, timeout=10) as response:
            if response.status == 200:
                try:
                    jsonData = await response.json()
                    async with aiofiles.open(fileOutput, "w", encoding="utf-8") as file:
                        await file.write(json.dumps(jsonData, indent=4))

                    print("[200] for {} by worker {}".format(statsLink, workerID))
                    return "success"
                except Exception as e:
                    print("Received non-JSON response for {} by worker {} (might be blocked)...".format(statsLink, workerID))
                    return "retry"

            elif response.status == 404:
                return "skip" # meet non-existent

            elif response.status == 403: # meaning website blocked temporarily
                print("[403] for {} by worker {}".format(statsLink, workerID))
                return "rotate the ip"

            else:
                print("[{}]. Something wrong for {} by worker {}".format(response.status, statsLink, workerID))
                return "retry"

    except Exception as e:
        print("Request failed for {} because of {} by worker {}".format(statsLink, e, workerID))
        return "retry"

async def worker(workerID, counter, retries):
    currentPassword = "initial"

    while True:
        meetID = await counter.nextID()
        if meetID is None: # forgot not also includes start of "0"
            break # no more

        for trial in range(retries):
            fileOutput = "../data/raw/meets/meet-{}-info.json".format(meetID)
            if os.path.exists(fileOutput):
                break

            # build new socket for each worker instead of sharing
            proxy = "socks5://worker_{}:{}@127.0.0.1:9050".format(workerID, currentPassword)
            connector = ProxyConnector.from_url(proxy)

            async with ClientSession(connector=connector) as session:
                result = await getMeet(session, meetID, workerID, fileOutput, retries)

                if result in ("success", "skip"):
                    break

                elif result == "rotate the ip":
                    currentPassword = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) # random
                    await asyncio.sleep(3)
                    continue

                elif result == "retry":
                    await asyncio.sleep(3)
                    continue

        await asyncio.sleep(2)

# worker-styled setup
async def main(start, total, retries=10):
    os.makedirs("../data/raw/meets", exist_ok=True)
    counter = IDCounter(start, total)

    print("Starting for meets from range {} to {}".format(start, total))
    tasks = [
        asyncio.create_task(worker(workerID=i, counter=counter, retries=retries))
        for i in range(numWorkers)
    ]

    await asyncio.gather(*tasks)
    print("Everything done!!")

if __name__ == "__main__":
    asyncio.run(main(start=1, total=int(8e5)))

'''
So basically,

- 50 workers run at once
- Each get their own IP address
- Each ping Milesplit only once per 2 seconds
- If errored out, it waits 5 seconds
- Gets meet data and downloads it
'''