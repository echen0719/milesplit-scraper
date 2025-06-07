# https://stackoverflow.com/questions/50197767
from aiohttp_socks import ProxyConnector
import asyncio
import aiohttp

# https://stackoverflow.com/questions/30286293
from stem import Signal
from stem.control import Controller

import time
import sys
from bs4 import BeautifulSoup

semaphore = asyncio.Semaphore(1000)

def newIdentity():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='') # SET PASSWORD HERE!
        controller.signal(Signal.NEWNYM)

async def getAthlete(session, i, trials=0):
    url = "https://www.milesplit.com/athletes/{}".format(i)
    while trials < 12: # 12 trials * 10 sec = 120 max to exit
        async with semaphore: # concurrent process limiter
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    name = soup.find('h1', {'id': 'athleteName'}) # find athlete name
                    if name:
                        print('Current Athlete: ' + str(i))
                        return str(i) + ". " + name.get_text(strip=True) + "\n"
                elif response.status == 403:
                    newIdentity()
                    # get new Tor identity and sleep
                    print('403...standby...10 seconds')
                    await asyncio.sleep(10)
                    trials += 1
                    continue
                elif response.status == 404:
                    return # if athlete doesn't exist, None is returned
                else # rarely ever happens
                    print("Try Again. Something wrong. Status Code: {}".format(response.status))
                    exit()
    print('Too many 403s') # basically the main cause for exit
    sys.exit(1) # 1 = general error

async def main():
    connector = ProxyConnector.from_url('socks5://127.0.0.1:9050') # seems to need from_url function
    # please continue