# Milesplit Data

Collection of scripts and files I used to get statistics for XCTF. Files are on Hugging Face, currently set to private access.

The goals of this project is to primarily to build dataset of athletic from [Milesplit](https://www.milesplit.com/) and perform statistical analysis and eventually, machine learning. This will be a long term project I will continue with.

## Project Structure

```
milesplit-scraper/
├── analysis/       # processing and analysis
├── archive/        # older/unused files
├── data/           # actual data/DBs
├── ml/             # machine learning + models
├── scraper/        # data collection
├── scripts/        # general util scripts
├── statistics/     # statistical analysis
...
└── schema.json     # declarative file of DBs
└── README.md
```

## Coverage

#### Latest dateset date: ```10/1/2026```
#### Historical dataset dates:
- 10/1/2026

More dates will be added as the dataset is expanded.

## Athlete Infomation:

This contains indivdual athlete data from [/api/v1/athletes](https://www.milesplit.com/api/v1/athletes/)

Total athlete count: ```16919708```

1. Most popular first names:
    - Michael (83992)
    - Jacob (83754)
    - Alex (83111)
    - Ryan (77204)
    - Andrew (75653)
2. Most popular surnames:
    - Smith (126318)
    - Johnson (110392)
    - Williams (96373)
    - Jones (80456)
    - Brown, 79929
3. Most popular events:
    - 5000m (26899014)
    - 100m (16483226)
    - 200m (15360708)
    - Shot Put (12747532)
    - 400m (11527560)
4. Most popular states (US only):
    - Texas (1305686)
    - California (1207468)
    - Florida (655280)
    - Ohio (650043)
    - New York (609828)

Analysis will include:
- Participation/number of races
  
## Teams Information:

This contains schools/teams data from [/api/v1/athletes/?teamId=](https://www.milesplit.com/api/v1/athletes/?teamId=)

- more statistics to come

## Meets Information:

This contains schools/teams data from ...

- more statistics to come

---

## Scraping Instructions:

**Requirements:**

Install the Python dependencies with:

```pip install aiohttp aiofiles aiohttp-socks stem``` 

Or install from your package manager

**Tor Configuration:**

Generate a Tor hashed password:

```bash
tor --hash-password <password>
```

Edit ```/etc/tor/torrc``` and add:
```
SOCKSPort 9050 IsolateSOCKSAuth
```

Restart the Tor service after.

**Running the scraper:**

```bash
python -u athleteInfoScraperV2.py > scraper.log 2>&1
```

This allows output to be directed to scraper.log to check for errors later (file will become ~1-2G).

**JSON output**:

Files that are scraped will be saved to ```./json/``` or in this case ```scraper/json/```

---

## Project Status

- [x] Athlete data collection
- [ ] Team data collection
- [ ] Meet data collection
- [ ] Cleaning data
- [ ] Statistical analysis
- [ ] Machine learning models

## Note:

This project is primarily intended for research purposes. Data was collected via public endpoints from Milesplit. DO NOT FLOOD THEIR SERVERS. This project is not sponsored by Milesplit.
