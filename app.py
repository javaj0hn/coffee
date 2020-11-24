from fastapi import FastAPI, Query

from urllib.request import urlopen
import urllib.error, json, math, re
from requests_html import HTML
import string, random, json
from utils.datetime_z import parse_datetime

# import configuration
from conf import config

app = FastAPI()

# random id generator
def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
      return ''.join(random.choice(chars) for x in range(size))

# concert list to dict
def convert(lst): 
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)} 
    return res_dct

@app.get('/')
def index():
    return {"status": "online"}

# osrs population
@app.get('/osrs/population')
def osrsPopulation():
    # make request to world select page
    try:
      response = urlopen(config["OSRS_WORLDSELECT_URL"])
    except urllib.error.HTTPError as e:
      return json.dumps(False)

    # decode response
    results = (response.read().decode('utf-8'))

    html = HTML(html=results)

    #rows = html.xpath('//*[@id="os-slu"]/div/div/main/section[2]/table/tbody/tr[*]')
    rows = html.xpath('//tr')

    # create list to store array
    data = []

    for row in rows:
      column = row.xpath('//td')
      if(column):
        try:
          worlds = {}
          # get int using regex, add 300 to get official world title
          worlds['world'] = int(re.search(r'\d+', column[0].text).group()) + 300
          worlds['population'] = int(re.search(r'\d+', column[1].text).group())
          worlds['location'] = column[2].text
          worlds['server'] = column[3].text
          worlds['activity'] = column[4].text
        
          # append to list
          data.append(worlds)
        except Exception as e:
          pass

    return json.dumps(data)

# osrs stat lookup
@app.get('/osrs/stats/{rsn}')
def osrsLookup(rsn: str):
    # check if rsn is empty
    if not rsn:
      return json.dumps(False)

    # check if rsn length too long
    if len(rsn) > 12:
        return json.dumps(False)

    # replace spaces with underscores
    rsn.replace(" ", "_")

    # make request to hiscores
    try:
      response = urlopen(config["OSRS_HISCORE_URL"] + rsn, data=None, timeout=60)
    except urllib.error.HTTPError as e:
      return json.dumps(False)

    if ("unavailable" in str(response)):
          return json.dumps(False)

    # decode response
    stats = (response.read().decode('utf-8')).replace(" ", "").replace("\n", ",")

    # check if rs hiscores is down - https://www.runescape.com/unavailable
    if ("this part of the website is currently unavailable" in stats):
          return json.dumps(False)

    # split strings by commas
    results = stats.split(',')

    # stats dict
    stats = {}

    # calculate combat
    meleeCombat = round(0.25 * (int(results[7]) + int(results[13]) + math.floor(int(results[19]) / 2  )) + 0.325 * (int(results[4]) + int(results[10])),2)
    rangeCombat = round(0.25 * (int(results[7]) + int(results[13]) + math.floor(int(results[19]) / 2  )) + 0.325 * math.floor((int(results[16]) / 2) + int(results[16])),2)
    magicCombat = round(0.25 * (int(results[7]) + int(results[13]) + math.floor(int(results[19]) / 2  )) + 0.325 * math.floor((int(results[22]) / 2) + int(results[22])),2)

    # assign values
    stats['status'] = True
    stats['rsn'] = rsn
    stats['combat_lvl'] = max(meleeCombat, rangeCombat, magicCombat)
    stats['attack_lvl'] = results[4]
    stats['attack_xp'] = results[5]
    stats['defence_lvl'] = results[7]
    stats['defence_xp'] = results[8]
    stats['strength_lvl'] = results[10]
    stats['strength_xp'] = results[11]
    stats['hitpoints_lvl'] = results[13]
    stats['hitpoints_xp'] = results[14]
    stats['ranged_lvl'] = results[16]
    stats['ranged_xp'] = results[17]
    stats['prayer_lvl'] = results[19]
    stats['prayer_xp'] = results[20]
    stats['magic_lvl'] = results[22]
    stats['magic_xp'] = results[23]
    stats['cooking_lvl'] = results[25]
    stats['cooking_xp'] = results[26]
    stats['woodcutting_lvl'] = results[28]
    stats['woodcutting_xp'] = results[29]
    stats['fletching_lvl'] = results[31]
    stats['fletching_xp'] = results[32]
    stats['fishing_lvl'] = results[34]
    stats['fishing_xp'] = results[35]
    stats['firemaking_lvl'] = results[37]
    stats['firemaking_xp'] = results[38]
    stats['crafting_lvl'] = results[40]
    stats['crafting_xp'] = results[41]
    stats['smithing_lvl'] = results[43]
    stats['smithing_xp'] = results[44]
    stats['mining_lvl'] = results[46]
    stats['mining_xp'] = results[47]
    stats['herblore_lvl'] = results[49]
    stats['herblore_xp'] = results[50]
    stats['agility_lvl'] = results[52]
    stats['agility_xp'] = results[53]
    stats['theiving_lvl'] = results[55]
    stats['theiving_xp'] = results[56]
    stats['slayer_lvl'] = results[58]
    stats['slayer_xp'] = results[59]
    stats['farming_lvl'] = results[61]
    stats['farming_xp'] = results[62]
    stats['runecrafting_lvl']  = results[64]
    stats['runecrafting_xp'] = results[65]
    stats['hunting_lvl'] = results[67]
    stats['hunting_xp'] = results[68]
    stats['contruction_lvl'] = results[70]
    stats['construction_xp'] = results[71]
    stats['overall_xp'] = results[0]

    return json.dumps(stats)