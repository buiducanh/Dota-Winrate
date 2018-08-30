import numpy as np
import json

with open("mapping/hero_id_to_roles.json", "r") as inp:
    id_to_roles = json.load(inp)

def extract_match_features(match):
    hero_choices = (np.zeros(114), np.zeros(114))
    hero_roles = (np.zeros(9), np.zeros(9))

    for player in match["players"]:
        offset = player["player_slot"] >> 7 # 0 for radiant, 1 for dire
        hero_id = player["hero_id"]
        hero_choices[offset][hero_id - 1] = 1
        for role in id_to_roles[str(hero_id)]:
            hero_roles[offset][role] += 1

    label = match["radiant_win"]
    return np.concatenate(hero_choices + hero_roles + ([label],))

dataset = []
for i in range(6):
    with open('./data/valid_matches_%d.json' % (i + 1), "r") as data:
        matches = json.load(data)
        for match in matches:
            features = extract_match_features(match)
            dataset.append(features)

dataset = np.array(dataset)
print dataset.shape
np.save("dota", dataset)
