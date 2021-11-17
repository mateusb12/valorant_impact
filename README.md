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
!rib matches -e 779 771 761 704 703 672 643 633 584 566502 457 435 418 105 377 
326 309 295 278 258 232 216 169 -csv
```

### `Generate link table (csv_manager.py)`
- Get a RIB .csv file (from discord) and convert it to a list of match links.
- In our example this is going to generate "na_links.csv"
```
ccr = CsvCreator("na.csv")
ccr.generate_link_table()
```

### `Split link table (csv_manager.py)`
- Since our "na_links.csv" is 151kb with more than 2000 matches, we're going to split it
- This is going to generate from "na_links_x.csv", with x ranging from "a" to "t"
- Each file has 8kb and 100 matches length
```
ccp = CsvSplitter("na_links.csv", file_amount=20)
ccp.split()
```

### `Download a single table link (scrap_matches.py)`
- In this example we're going to download "na_links_a.csv" links
- You can start multiple runs at the same time ("threads") by doing the following
```
- Change second parameter value from "a" to "b" → right click -> run file in python console
```
- In our example each file takes 4 minutes to be fully downloaded.
- You can increase the speed by "threading" everything at once
- JSON files will be downloaded in [webscrapping/matches/jsons]
```
download_run("na_links", "a")
```

### `Merge all CSVs (csv_manager.py)`
- After almost 1 hour we finally managed to download all of our matches
- This generated a JSON folder with 2,241 files and 880 MB
- Let's convert everything into a single csv dataset (combined_na.csv)
- obs: some files main contain inconsistencies. For instance, 12875.json only had 9 players instead of 10. So I had to delete that file. You can check that match here: https://rib.gg/series/7386?match=12875&round=1&tab=round-stats
```
cm = CsvMerger("na_merged.csv", delete_jsons=False)
cm.merge()
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
