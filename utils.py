import json
import shutil

from interactions import *
import requests
from pathlib import Path

config={  
	"token":""
}  

def saveConfig(c):
	global config
	print("save config file")
	config = c
	with open("config.json", "w") as outfile:
		json.dump(c, outfile, indent=4)

def loadConfig():
		global config
		print("Loading config file")
		with open('config.json', 'r') as openfile:
			config = json.load(openfile)
			return config
			
def rgb_to_hex(rgb: list):
	return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def is_the_same_author(component: BaseComponent, author: Member | User) -> bool:
	return component.ctx.author.id == author.id

def art_suggestion_get_coord(message: Message):
	try:
		value = [x.split(" ") for x in message.embeds[0].fields[1].value.split(",")]
		return [int(value[0][2]),int(value[1][3])]
	except:
		return None
	
async def DisabledArtActionRow(message : Message, bool: bool):
	components = message.components

	for ActionRow in components:
		for component in ActionRow.components:
			try:
				component.disabled = bool
			except:
				print(component.type)

	await message.edit(components=components)
	
def is_int(s):
	try: 
		int(s)
	except ValueError:
		return False
	else:
		return True

def get_id_using_mention(a:str):
    a = a.replace("<","")
    a = a.replace(">","")
    a = a.replace("@","")
    return a

def download_image(url, author, name, scale):
	r = requests.get(url, stream=True)
	if r.status_code == 200:
		Path(f'./Images/{author}/{name}').mkdir(parents=True, exist_ok=True)
		with open(f'./Images/{author}/{name}/{scale}.png', 'wb') as f:
			r.raw.decode_content = True
			shutil.copyfileobj(r.raw, f)