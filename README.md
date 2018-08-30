Code to collect data and train a classifier that predict a Dota 2 match win loss based on the team composition>

# Paper report
For anyone interested in the paper report, please contact the author of this repo.

# Reproduction Notes

Data collections and feature extractions are in data_collect.py and feature_extract.py

data_collect.py:
  This file talks with Valve API to get the game data. About 100000 matches on roughly mid-April 2017. However, it first checks for caches of data (using file names) before actually making api calls. After the matches data are available, the matches are processed in batches to filter out high-quality matches as described in the paper. Finally all the valid matches are saved in 10000 matches increments as "data/valid_matches_[number].json"

feature_extract.py:
  This file uses mappings in "mapping/" and data in "data/" to create feature vectors with labels that eventually become "dota.npy"

The learning and plotting part are in the two files learn.py and plot.py. RUN THEM IN THAT ORDER TO REPRODUCE, because learn.py persists "results.json" that is eventually used by plot.py
