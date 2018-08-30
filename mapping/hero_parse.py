import json
import requests
import os
import dota2api

def map_name_to_id(heroes):
    res = {}
    for hero in heroes:
        res[hero["name"]] = hero["id"]
    return res

def map_hero_roles(heroes, roles, heropedia):
    out = "hero_id_to_roles.json"
    if os.path.isfile(out): return
    res = {}
    name_to_id = map_name_to_id(heroes)

    for key, value in heropedia.iteritems():
        hero_roles = list(map(lambda x: roles[x], value["droles"].split(" - ")))
        res[name_to_id[key]] = hero_roles

    with open(out, "w") as f:
        json.dump(res, f)


api = dota2api.Initialise()

persist_file = "heroes.json"
if not os.path.isfile(persist_file):
    resp = api.get_heroes()
    heroes = resp["heroes"]

    # drop npc_dota_hero_
    for hero in heroes:
        hero["name"] = hero["name"].split("npc_dota_hero_")[1]

    with open(persist_file, 'w') as out:
        json.dump(heroes, out)
else:
    with open(persist_file, 'r') as inp:
        heroes = json.load(inp)

persist_file = "heropedia.json"
if not os.path.isfile(persist_file):
    heropedia = requests.get('http://www.dota2.com/jsfeed/heropediadata?feeds=herodata').json()['herodata']

    with open(persist_file, 'w') as out:
        json.dump(heropedia, out)
else:
    with open(persist_file, 'r') as inp:
        heropedia = json.load(inp)

with open("heroes_role.json", "r") as inp:
    roles = json.load(inp)

map_hero_roles(heroes, roles, heropedia)
