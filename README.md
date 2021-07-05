# Valorant Data Science
_Predicting the round outcomes_



## Webscrapping
- Entirely done on BS4
- Data scrapped from RunItBack 2d replay feature

Getting all matches IDs by giving the RIB discord bot the event IDs (br.csv) 

```sh
!rib matches -e 529 526 502 472 470 442 438 417 410 428 401 366 361 202 335 297 338 292 267 263 262 230 213 176 175 147 99 -csv
```
Creating a CSV with all matches HTTP links based on the csv above
```
rb.generate_links("br.csv")
```
Downloading JSONs from the csv above (webscrapping/matches/json)
```
rb.download_links("br_links.csv")
```
Converting that new JSON folder into a single csv dataset (combined_br.csv)
```
merge_all_csv('combined_br.csv')
```

## Current game state
- Wealth (weapon price + abilities)
- Shields
- Regular time (from the barriers drop to the current timestamp)
- Spike time (from the plant to the current timestamp)
- Duelists (amount of duelists alive)
- Initiators (amount of initiators alive)
- Controllers (amount of controllers alive)
- Sentinels (amount of sentinels alive)
- Whether the defense has Odin
- Whether the defense has Operator
- Map being played

All these variables are used as an input to a machine learning model, which evaluates the current probability of the **attacking side** to win that round.

More details on the jupyter notebooks
