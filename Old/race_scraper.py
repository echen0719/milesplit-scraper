import requests
import time
from bs4 import BeautifulSoup

def heatScrape(raceCompleteLink, fileOutput):
    response = requests.get(raceCompleteLink)

    if response.status_code == 200:
        heatResult = response.text.split("<pre>")[1].split("</pre>")[0]
        # example text<pre>hi there</pre>more example text
        # ['example text', 'hi there </pre> more example text'] --> index 1
        # ['hi there', 'more example text] --> index 0
        # result is 'hi there'

        content = '\n'.join([line.strip() for line in heatResult.splitlines()])
        # https://stackoverflow.com/questions/31218253/trim-whitespace-from-multiple-lines
        # really helped me

        with open(fileOutput, mode='a') as file:
                file.write(content)

    else:
        print(f"Try Again. Something wrong. Status Code: {response.status_code}")
        exit()

def getHeatLinks(raceNestedLinks):
    response = requests.get(raceNestedLinks)

    if response.status_code == 200:
        heat = []
        # I think bs4 is easier to work with for this part
        soup = BeautifulSoup(response.text, 'html.parser')
        anchors = soup.find('ul', {'id': 'resultFileList'}).find_all('a') # find list of <a> in <ul> with ID resultFileList

        for anchor in anchors: # need raw instead of formatted
            heat.append(anchor.get('href').replace('/formatted/', '?type=raw'))
        return heat # returns a list

    else:
        print(f"Try Again. Something wrong. Status Code: {response.status_code}")
        exit()

def main():
    for heat in getHeatLinks("https://nj.milesplit.com/meets/624764-shore-coaches-invitational-2024/results"): # seems to work
        heatScrape(heat, "coaches-invitational-results.txt")
        time.sleep(2)

if __name__ == "__main__":
    main()
