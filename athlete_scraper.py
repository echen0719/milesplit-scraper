import requests
import time
from bs4 import BeautifulSoup

# gets the levels the athlete has partipcated in
# for instance, using my profile will return ['High School']

def getLevels(athlete):
    response = requests.get(athlete)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        levels = []

        for level in soup.find_all('div', {'class': 'record-box'}): # gets all div elements with classes 'record-box'
            for head in level.find_all('h5', {'class': 'box-heading'}): # gets all h5 elements with classes 'box-heading'
                heading = head.get_text(strip=True) # this should take the text inside the element
                if heading not in levels and heading != 'College Progression Tracker': # short-circuit, I think
                    levels.append(heading)

        return levels

    elif response.status_code == 404:
        return # some profiles don't exist like https://www.milesplit.com/athletes/{9 through 14}

    else:
        print(f"Try Again. Something wrong. Status Code: {response.status_code}")
        exit()

def getNames(athlete):
    response = requests.get(athlete)

    if response.status_code == 200:
       soup = BeautifulSoup(response.text, 'html.parser')
       return soup.find('h1', {'id': 'athleteName'}).get_text(strip=True)

    elif response.status_code == 404:
        return

    else:
        print(f"Try Again. Something wrong. Status Code: {response.status_code}")
        exit()

def main():
    with open("all-athlete-names.txt", mode='a') as file:
        for i in range(1, 16268836): # currents max athlete MS has
            athlete = "https://www.milesplit.com/athletes/{}".format(i)
            name = getNames(athlete)
            if name:
                file.write(str(i) + ". " + name + "\n")

if __name__ == "__main__":
    main()
    # pass

# print(getLevels("https://www.milesplit.com/athletes/13822077"))
# test athlete 1 would return ['2025 Indoor Rankings', '2024 Indoor Rankings', 'High School']
# print(getLevels("https://www.milesplit.com/athletes/15218721"))
# test athlete 2 (me) would return ['High School']

# print(getNames("https://www.milesplit.com/athletes/13822077"))
# test athlete 1 would return 'Raghu Moorthy'
# print(getNames("https://www.milesplit.com/athletes/15218721"))
# test athlete 2 would return 'Eric Chen'
