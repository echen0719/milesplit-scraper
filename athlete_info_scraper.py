import asyncio
import aiohttp
import aiofiles # for dumps
import json
import sys

# all TOR
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

# for swapping TOR connections
from stem import Signal
from stem.control import Controller

if len(sys.argv) != 2:
    print("Set the TOR password by: \n")
    print("python {} <your TOR password>".format(sys.argv[0]))
    exit(1)

torProxy = "socks5://127.0.0.1:9050"
torPassword = sys.argv[1] # SET PASSWORD HERE!

async def newTORIdentity():
    def renew():
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password=torPassword)
                controller.signal(Signal.NEWNYM)
        except:
            print("Tor failed to change identity")

    await asyncio.to_thread(renew) # made everything including this async

# internet can handle this
# 300 * ~4KB = 1.2 MB every few seconds
semaphore = asyncio.Semaphore(300)

async def getAthlete(session, athleteID, retries=10):
    statsLink = "https://www.milesplit.com/api/v1/athletes/{}/stats".format(athleteID)
    fileOutput = "athlete-{}-stats.json".format(athleteID)

    # maximum time is 100 seconds in case I get unlucky and pull a bunch of slow TOR networks
    async with semaphore:
        trials = 0

        while trials < retries:
            try:
                async with session.get(statsLink, timeout=10) as response:
                    if response.status == 200:
                        print("[200] for {}".format(statsLink))
                        try:
                            jsonData = json.dumps(await response.json(), indent=4)
                            async with aiofiles.open(fileOutput, "w", encoding="utf-8") as file:
                                await file.write(jsonData)
                            return
                        except:
                            print("Received non-JSON response (possibly blocked).")
                            await newTORIdentity()
                            await asyncio.sleep(10)
                    elif response.status == 403: # meaning website blocked temporarily
                        print("[403] for {}. Waiting 10 seconds before proceeding".format(statsLink))
                        await newTORIdentity()
                        await asyncio.sleep(10)
                    elif response.status == 404:
                        return None # athlete non-existent
                    else:
                        print("[{}]. Something wrong for {}".format(response.status, statsLink))
                        await asyncio.sleep(180) # let's say all networks were throttled, we wait 3 min
            except Exception as e:
                print("Request failed for {} because of {}".format(statsLink, e))

            trials += 1

# batched setup
async def main(total, batchSize=1000000, chunkSize=32768, retries=10):
    connector = ProxyConnector.from_url(torProxy)

    async with ClientSession(connector=connector) as session:
        for start in range(0, total, batchSize):
            end = min(start + batchSize, total)
            print("Doing batch for athlete IDs of {} to {}".format(start, end))

            for i in range(start, end, chunkSize):
                tasks = [getAthlete(session, athleteID) for athleteID in range(i, min(i + chunkSize, end))]
                await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main(total=int(1.9*10**7)))