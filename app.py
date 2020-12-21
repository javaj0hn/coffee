from fastapi import FastAPI, Query
from typing import Optional
import attr
from urllib.request import urlopen
import urllib.error, json, math, re
from requests_html import HTML
import string, random, json
from utils.datetime_z import parse_datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from discord_webhook import DiscordWebhook
import os

# import configuration
from conf import config

# import db
from db import db

app = FastAPI()

class XPTracker(BaseModel):
	clan_name: str = None
	event_name: str = None
	server: str = None
	members: list = None

class XPTrackEnd(BaseModel):
	token: str = None

class Account(BaseModel):
	rsn: str = None

class TrackedAccount(BaseModel):
	rsn: str = None
	attack_xp: int = None
	strength_xp: int = None
	hitpoints_xp: int = None
	ranged_xp: int = None
	magic_xp: int = None

class MemberlistUpdate(BaseModel):
	invalid: list = None

class DrunkCoinEnroll(BaseModel):
	discord_id: str = None
	balance: int = 10

# random id generator
def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
      return ''.join(random.choice(chars) for x in range(size))

# concert list to dict
def convert(lst): 
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)} 
    return res_dct

# validate and clean rsn
def rsnValidateClean(rsn: str):
	# check if rsn is empty
	if not rsn:
		return json.dumps(False)
	  
	# check if rsn length too long
	if len(rsn) > 12:
		return json.dumps(False)
		
	# replace spaces with underscores
	rsn.replace(" ", "_")

	return rsn

@app.get('/')
def index():
    return {"status": "online"}

@app.post('/osrs/legacy/webhook')
def callWebHook(body: MemberlistUpdate):
	# fetch invalid users
	with urllib.request.urlopen("https://legacy-rs.org/coffee/invalid.json") as url:
		data = json.loads(url.read().decode())
		print(data)
	# fetch new avgs?

	# send webhook with payload
	#webhook = DiscordWebhook(url=os.environ.get('ly_webhook'), content='Memberlist Updated! ~ https://legacy-rs.org/memberlist/')
	#response = webhook.execute()
	return True

@app.post('/osrs/track/s/clan')
def osrsTrackClanXP(body: XPTracker):

	# generate token
	token = random_generator()

	# loop through users and look up stats
	memberStats = []
	invalidAccounts = []

	# append event headers
	eventHeader = {
		"token": token,
		"clan_name": body.clan_name,
		"event_name": body.event_name,
		"server": body.server
	}
	memberStats.append(eventHeader.copy())

	for rsn in body.members:
		print("Looking up: " + rsn)
		with urllib.request.urlopen("http://localhost:8000/osrs/stats/" + rsn) as url:
			data = json.loads(url.read().decode())
			if (data['status'] == True):
				memberStats.append(data.copy())
			elif (data['status'] == False):
				invalidAccounts.append(rsn)
			else:
				invalidAccounts.append(rsn)

	# write to json
	if memberStats:
		with open("data/xptracker/" + token + ".json", 'w') as fp:
			json.dump(memberStats, fp)

	data = {
		"token": token,
		"invalidAccounts": invalidAccounts
	}

	return JSONResponse(content=data)

@app.post('/osrs/track/e/clan')
def osrsEndTrackClanXP(body: XPTrackEnd):
	with open("data/xptracker/" + body.token + ".json", 'r') as f:
		starting = json.load(f)
	
	if starting:

		results = []
		invalidAccounts = []

		# add event header
		eventHeader = {
			"token": body.token,
			"event_details": starting[0]
		}
		results.append(eventHeader.copy())

		# loop & skip first row
		for player in starting[1:]:
			with urllib.request.urlopen("http://localhost:8000/osrs/stats/" + player['rsn']) as url:
				ending = json.loads(url.read().decode())
			if (ending['status'] == True):
				gains = {
					"rsn": ending['rsn'],
					"overall_xp": int(ending['overall_xp']) - int(player['overall_xp']),
					"attack_xp": int(ending['attack_xp']) - int(player['attack_xp']),
					"strength_xp": int(ending['strength_xp']) - int(player['strength_xp']),
					"defence_xp": int(ending['defence_xp']) - int(player['defence_xp']),
					"hitpoints_xp": int(ending['hitpoints_xp']) - int(player['hitpoints_xp']),
					"ranged_xp": int(ending['ranged_xp']) - int(player['ranged_xp']),
					"magic_xp": int(ending['magic_xp']) - int(player['magic_xp']),
					"snare_count": round(((int(ending['magic_xp']) - int(player['magic_xp'])) / 60))
				}
				results.append(gains.copy())
			
			# if rsn does not exist
			elif (ending['status'] == False):
				invalidAccounts.append(rsn)
			else:
				invalidAccounts.append(rsn)


		# TODO: after looping, do we retry invalid accounts?

		# calc averages & overall gains
		overallStats = {
			"overall_xp": 0,
			"attack_xp": 0,
			"strength_xp": 0,
			"defence_xp": 0,
			"hitpoints_xp": 0,
			"ranged_xp": 0,
			"magic_xp": 0,
			"snare_count": 0
		}
		for r in results[1:]:
			overallStats['overall_xp'] += int(r['overall_xp'])

		print(overallStats)

		# write to json file
		with open("data/xptracker/results_" + body.token + ".json", 'w') as fp:
			json.dump(results, fp)

	# delete starting json?

	return JSONResponse(content=results)

# enroll user into DrunkCoin
@app.post('/drunkcoin/enroll/')
def dcEnroll(body: DrunkCoinEnroll):
	data = db.enrollUser(body)
	return JSONResponse(content=data)

# get drunkcoin leaderboard
@app.get('/drunkcoin/leaderboard')
def dcLeaderboard():
	data = db.getLeaderboard()
	return JSONResponse(content=data)

# get drunkcoin balance
@app.get('/drunkcoin/balance/{discord_id}')
def dcBalance(discord_id: str):
	data = db.getBalance(discord_id)
	return JSONResponse(content=data)

# get drunkcoin active fights
@app.get('/drunkcoin/a/fights')
def dcActiveFights():
	data = db.getFights()
	return JSONResponse(content=data)

# get drunkcoin fight results
@app.get('/drunkcoin/r/fights')
def dcFightResults():
	return

# osrs population
@app.get('/osrs/population')
def osrsPopulation():
    # make request to world select page
    try:
      response = urlopen(config["OSRS_WORLDSELECT_URL"])
    except urllib.error.HTTPError as e:
      return JSONResponse({"status": False, "msg": "Unable to fetch population"})

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

    return JSONResponse(content=data)

# osrs stat lookup
@app.get('/osrs/stats/{rsn}')
def osrsLookup(rsn: str):
	rsn = rsnValidateClean(rsn)

	if rsn is None:
		return JSONResponse({"status": False, "msg": "RSN Empty or Invalid"})
	# make request to hiscores
	try:
		response = urlopen(config["OSRS_HISCORE_URL"] + rsn, data=None, timeout=60)
	except urllib.error.HTTPError as e:
		return JSONResponse({"status": False, "msg": "Hiscores currently down"})	
	if ("Nothing interesting happens" in str(response)):
		return JSONResponse({"status": False, "msg": "RSN does not exist"})
	if ("unavailable" in str(response)):
	      return JSONResponse({"status": False, "msg": "Hiscores currently down"})	
	# decode response
	stats = (response.read().decode('utf-8')).replace(" ", "").replace("\n", ",")	
	# check if rs hiscores is down - https://www.runescape.com/unavailable
	if ("this part of the website is currently unavailable" in stats):
	      return JSONResponse({"status": False, "msg": "Hiscores currently down"})	
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
	stats['overall_xp'] = results[2]	
	return JSONResponse(content=stats)