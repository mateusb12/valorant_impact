# Valorant Data Science
_Predicting the round outcomes_

## Webscrapping
- Entirely done on BS4
- Data scrapped from RunItBack 2d replay feature

### `Get events (discord command)`
- Let's get the events to which the current best 12 liquipedia NA teams attended
![](https://i.imgur.com/NbPdH6x.png)
```
!rib events -t 388 75 305 141 603 318 417 1931 617 278 281 279 116 -csv
```
### `Get all matches (discord command)`


- Getting all matches IDs by giving the RIB discord bot the event IDs. 
- Since the amount of events in our previous .csv is high we're going to handpick some big events.
- This is going to generate a file called [na.csv], which should be put in [webscrapping/matches/events]

```sh
!rib matches -e 779 771 761 672 643 502 -csv
```

### `Generate and download all links (scrap_matches.py)`
- This will create a .csv with lots of links to the matches.
- There is an option to download them using threads in order to increase the speed
- JSON files will be put in [webscrapping/matches/jsons]
```
ms = MatchScrapper("na.csv")
ms.download_all_matches(assync=True)
```

### `Merge all CSVs`
- Converting that new JSON folder into a single csv dataset (combined_br.csv)
```
ms.merge_jsons_into_csv("na_merged.csv", delete_json=True)
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

![](https://i.imgur.com/Izinsiy.png)

## Case study (Furia vs Highpower)

![](https://pbs.twimg.com/media/E4rd2w5WQAU3Vjq?format=png&name=small)

After losing a gunround where not a single defender managed to save his gun, FURIA boys got an economical collapse. We are talking about 4 pistols + 1 stinger against 5 vandals, which leads us to a small chance of 19,5% of FURIA winning that round.

![](https://i.imgur.com/xV2xRVm.png)

No multikill. No clutch. No highlight. With only 2 frenzy kills, our "manito" Nozwerr managed to turn an impossible round **(19,5%)** into a plausible one  **(60,6%)**. Indisputably, the player with the most impact in this Ascent round.

In Valorant there are MANY kills that does not bring any impact to the round but that are there to inflate ACS and other useless stats. Nozwerr could have a much bigger KDA if he went mid on antieco rounds in order to hunt frags against classics/sheriffs, but according to our model his impact % ratio would be pretty much the same.
