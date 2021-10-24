# Valorant Data Science
_Predicting the round outcomes_

## Webscrapping
- Entirely done on BS4
- Data scrapped from RunItBack 2d replay feature

### `Get all matches (discord command)`


- Getting all matches IDs by giving the RIB discord bot the event IDs (br.csv) 

```sh
!rib matches -e 529 526 502 472 470 442 438 417 410 428 401 366 361 202 335 297 338 292 267 263 262 230 213 176 175 147 99 -csv
```

### `Generate all links`
- Creating a CSV with all matches HTTP links based on the csv above
```
rb.generate_links("br.csv")
```

### `Download all links`
- Downloading JSONs from the csv above (webscrapping/matches/json)
```
rb.download_links("br_links.csv")
```

### `Merge all CSVs`
- Converting that new JSON folder into a single csv dataset (combined_br.csv)
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

![](https://i.imgur.com/C6knfE2.png)

## Case study (Furia vs Highpower)

![](https://pbs.twimg.com/media/E4rd2w5WQAU3Vjq?format=png&name=small)

After losing a gunround where not a single defender managed to save his gun, FURIA boys got an economical collapse. We are talking about 4 pistols + 1 stinger against 5 vandals, which leads us to a small chance of 19,5% of FURIA winning that round.

![](https://i.imgur.com/xV2xRVm.png)

No multikill. No clutch. No highlight. With only 2 frenzy kills, our "manito" Nozwerr managed to turn an impossible round **(19,5%)** into a plausible one  **(60,6%)**. Indisputably, the player with the most impact in this Ascent round.

In Valorant there are MANY kills that does not bring any impact to the round but that are there to inflate ACS and other useless stats. Nozwerr could have a much bigger KDA if he went mid on antieco rounds in order to hunt frags against classics/sheriffs, but according to our model his impact % ratio would be pretty much the same.
