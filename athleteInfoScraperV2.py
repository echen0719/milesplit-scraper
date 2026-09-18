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

async def getAthlete(session, athleteID, workerID, retries):
    statsLink = "https://www.milesplit.com/api/v1/athletes/{}/stats".format(athleteID)
    fileOutput = "json/athlete-{}-stats.json".format(athleteID)

    # since this script may be run multiple times to not overwrite already found athletes
    if os.path.exists(fileOutput):
        return "already there"

    try:
        async with session.get(statsLink, timeout=10) as response:
            if response.status == 200:
                try:
                    jsonData = json.dumps(await response.json(), indent=4)
                    async with aiofiles.open(fileOutput, "w", encoding="utf-8") as file:
                        await file.write(jsonData)
                    print("[200] for {} by worker {}".format(statsLink, workerID))
                    return "success"
                except Exception as e:
                    print("Received non-JSON response for {} by worker {} (might be blocked)...".format(statsLink, workerID))
                    return "retry"

            elif response.status == 404:
                return "skip" # athlete non-existent

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
        athleteID = await counter.nextID()
        if athleteID is None: # forgot not also includes start of "0"
            break # no more

        for trial in range(retries):
            # build new socket for each worker instead of sharing
            proxy = "socks5://worker_{}:{}@127.0.0.1:9050".format(workerID, currentPassword)
            connector = ProxyConnector.from_url(proxy)

            async with ClientSession(connector=connector) as session:
                result = await getAthlete(session, athleteID, workerID, retries)

                if result in ("success", "already there", "skip"):
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
    os.makedirs("json", exist_ok=True)
    counter = IDCounter(start, total)

    print("Starting for athletes from range {} to {}".format(start, total))
    tasks = [
        asyncio.create_task(worker(workerID=i, counter=counter, retries=retries))
        for i in range(numWorkers)
    ]

    await asyncio.gather(*tasks)
    print("Everything done!!")

if __name__ == "__main__":
    asyncio.run(main(start=1, total=int(2*10**7)))

'''
So basically,

- 50 workers run at once
- Each get their own IP address
- Each ping Milesplit only once per 2 seconds
- If errored out, it waits 5 seconds
- Gets athlete data and downloads it
'''