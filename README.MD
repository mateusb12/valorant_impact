# Valorant Impact
Valorant impact is a project where we fed a machine learning model with thousands of VCT matches in order to evaluate how likely attackers are of winning a round at any given situation. 

- We created a gamestate variable, where we store multiple features (team loadout, sentinels alive, team compaction, etc)
- Players can take actions that may impact on this gamestate (by killing an enemy, by planting the spike, etc)
- With the new gamestate running on, we have new probabilities on the table. The higher the probability shift is, the bigger the impact is involved in that play

**Main pipeline**
- Go to RIB match page, and get the match identifiers as the picture below
![sample image](https://i.imgur.com/VCwWvrz.png)

- Go to webscrapping/rib_scrapper.py and input values for matchID and seriesID on the function

![sample image](https://i.imgur.com/18ExPfS.png)

- Done!

![sample image](https://i.imgur.com/LPe0UBw.png)

- Once you have downloaded the json file, go to impact_score/impact/plot.ipynb and input the round you want
- and the team side (attack or defense)

![sample image](https://i.imgur.com/J2GOnYz.png)

- Done!
![sample image](https://i.imgur.com/fHw5F6w.png)