import asyncio
import json
import shutil
from interactions import *
import requests
from pathlib import Path

from TOKEN import TOKEN
from utils import loadConfig, saveConfig, config

######################################################################################################################################################
####################### MISC related code
######################################################################################################################################################
loadConfig()
bot = Client()

def loadData(path: str):
	with open(f'{path}/Data.json', 'r') as openfile:
		Data = json.load(openfile)
	return Data

def saveData(path: str, Data: dict[str]):
	Path(path).mkdir(parents=True, exist_ok=True)
	with open(f"{path}/Data.json", "w") as outfile:
		json.dump(Data, outfile, indent=4)
	
def checkBotConfig():

	if(config["PlaceModoRole"] == 0):
		print("ERROR : An admin role need to be set using this command `/bot set admin-role`, everything has been diable.")
		config['IsArtSuggestionBotEnable'] = False
		saveConfig()

	if(config['botLogChannelId'] == 0): # If the bot haven't the log channel disable everything.
		print("ERROR : The Bot doesn't have a Log Channel, plz setup one using `/bot set log-channel`, everything has been diable.")
		config['IsArtSuggestionBotEnable'] = False
		saveConfig()

def download_image(url, author, name, scale):
	r = requests.get(url, stream=True)
	if r.status_code == 200:
		Path(f'./Images/{author}/{name}').mkdir(parents=True, exist_ok=True)
		with open(f'./Images/{author}/{name}/{scale}.png', 'wb') as f:
			r.raw.decode_content = True
			shutil.copyfileobj(r.raw, f)

@listen()
async def on_startup():
	print("Bot is ready!")

	# checkBotConfig()

######################################################################################################################################################
####################### BOT commande
######################################################################################################################################################

bot_command = SlashCommand(name="bot", description="All bot commands")

@bot_command.subcommand(
	group_name="set",
	group_description="Set the value of something.",
	sub_cmd_name="log-channel", 
	sub_cmd_description="Setup the log channel to use for the bot.",
		options= [
		{
			"name": "channel",
			"description": "The channel to use as log channel for the bot",
			"type": 7,
			"required": "true"
		}
	]
)
async def botSetLogChannel(ctx: SlashContext, channel):
	if(ctx.author.id != ctx.guild.get_owner().id):
		ctx.send(f"ERROR : You don't have the permission to use this command.", ephemeral=True)
	global config
	await ctx.send(f"log channel set to : {channel.name}, a message have been send in this channel, if you don't see it, look the perm of the channel")
	await bot.get_channel(channel.id).send(f"{ctx.author.mention} execute `/bot set log-channel`.\nThis Channel are going to be used as log channel for me.")
	config["botLogChannelId"]= channel.id
	saveConfig()

@bot_command.subcommand(
	group_name="set",
	group_description="Set the value of something.",
	sub_cmd_name="admin-role", 
	sub_cmd_description="Setup the admin role, that can use bot admin function.",
		options= [
		{
			"name": "role",
			"description": "The role to use as Admin role for the admin command",
			"type": OptionType.ROLE,
			"required": "true"
		}
	]
)
async def botSetAdminRole(ctx: SlashContext, role):
	if(ctx.author.id != ctx.guild.get_owner().id):
		ctx.send(f"ERROR : You don't have the permission to use this command.", ephemeral=True)
	global config
	await ctx.send(f"This role : {role.name}, have now the permission to use the admin command.", ephemeral=True)
	await bot.get_channel(config["botLogChannelId"]).send(f"{ctx.author.mention} execute `/bot set admin-role`.\nThis role : {role.name}, have now the permission to use the admin R/Place command.")
	config["PlaceModoRole"] = role.id
	saveConfig()

######################################################################################################################################################
####################### Place commande
######################################################################################################################################################

place = SlashCommand(name="place", description="All R/Place commands")
# group = place.group(name="group", description="Plce")

@place.subcommand(
	sub_cmd_name="start", 
	sub_cmd_description="Set when the event R/Place start.",
	options= [
		{
			"name": "seconds",
			"description": "The time in seconds to wait",
			"type": 4,
			"required": "true"
		}
	]
)
async def PlaceStart(ctx: SlashContext, seconds):
	try:
		secondint = int(seconds)
		if secondint > 300:
			await ctx.send("I dont think im allowed to do go above 300 seconds.")
			raise BaseException
		if secondint <= 0:
			await ctx.send("I dont think im allowed to do negatives")
			raise BaseException
		message = await ctx.send(f"Timer: {seconds}")
		while True:
			secondint -= 1
			if secondint == 0:
				await message.edit(content="Ended!")
				break
			await message.edit(content=f"Timer: {secondint}")
			await asyncio.sleep(1)
		await ctx.send(f"{ctx.author.mention} Your countdown Has ended!")
	except ValueError:
		await ctx.send("Must be a number!")
	await ctx.send("Place start.")

# @place.subcommand(sub_cmd_name="force_start", sub_cmd_description="Force Start the event R/Place now.")
# async def PlaceForceStart(ctx: SlashContext):
# 	await ctx.send("Place force start.")

######################################################################################################################################################
####################### Art commande
######################################################################################################################################################

ArtValidationEmbed = Embed(
	title="your title",
	description="your description",
	color="#1DCDE1"
)

ArtSuggestionButtonSubmitArt = Button(
	style=ButtonStyle.PRIMARY,
	label="Submit a new art",
	emoji=":star2:",
	custom_id="ArtSuggestionButtonSubmitArt",
	disabled=False
)


art = SlashCommand(name="art", description="All Art sugestion commands")

@art.subcommand(
	group_name="set",
	group_description="Set the value of something.",
	sub_cmd_name="enable", 
	sub_cmd_description="Enable the art suggestio system for the R/Place ?",
		options= [
		{
			"name": "value",
			"description": "Enbale the art suggestion.",
			"type": 5,
			"required": "true"
		}
	]
)
async def artEnable(ctx: SlashContext, value):
	global config
	if(value):
		# if(config['ArtValidationChannelId'] == 0):
		#	 await ctx.send("Plz give a channl for the Art validation channel using this command `/art set art-validation-channel`")
		#	 return

		if(config['botLogChannelId'] == 0):
			await ctx.send("Plz give a channl for the bot is log using this command `/bot set log-channel`")
			return

		await ctx.send("The Art suggestion bot is enable.")
		isgood = await setupArtSuggestionBot(ctx)

	else:
		await ctx.send("The Art suggestion bot is disable.")
		isgood = await resetArtSuggestionBot()

	if(isgood):
		config["IsArtSuggestionBotEnable"] = value
	saveConfig()

async def setupArtSuggestionBot(ctx = None):
	global config
	print("Setup")
	if(config['ArtValidationChannelId'] != 0):
		channel = bot.get_channel(config['ArtValidationChannelId'])
		post = await channel.create_post(
			content=None,
			name="Create a suggestion.", 
			embed=ArtValidationEmbed,
			components=[ArtSuggestionButtonSubmitArt]
		)
		await post.pin()
		config["MessageTutoForArtSuggestionId"]=post.id
	else : 
		if(ctx != None):
			await ctx.send("Art Validation channel isn't set, plz set it before enableing the art suggestion bot, the bot is diable")
		else :
			await bot.get_channel(config['botLogChannelId']).send("Art Validation channel isn't set, plz set it before enableing the art suggestion bot, the bot is diable")
		config["IsArtSuggestionBotEnable"] = False
		return False
	saveConfig()
	return True

async def resetArtSuggestionBot():
	print("reset")
	if(config["MessageTutoForArtSuggestionId"] != 0):
		await bot.get_channel(config["ArtValidationChannelId"]).get_post(config["MessageTutoForArtSuggestionId"]).delete()
	return True


@art.subcommand(
	group_name="set",
	group_description="Set the value of ...",
	sub_cmd_name="art-validation-channel", 
	sub_cmd_description="Set the channel to use for the art validation.",
	options= [
		{
			"name": "channel",
			"description": "Try",
			"type": 7,
			"required": "true"
		}
	]
)
async def artSetArtValidationChannelId(ctx: SlashContext, channel):
	global config
	await ctx.send(str(channel.id))
	if(config["ArtValidationChannelId"] != channel.id):
		if(config["MessageTutoForArtSuggestionId"] != 0):
			post = bot.get_channel(config["ArtValidationChannelId"]).get_post(config["MessageTutoForArtSuggestionId"])
			await post.delete(reason="The channel to use change.")
			config["MessageTutoForArtSuggestionId"] = 0
	config["ArtValidationChannelId"] = channel.id
	if(config["IsArtSuggestionBotEnable"]):
		await setupArtSuggestionBot()
	#await ctx.send(str(ctx.member.guild.id))
	saveConfig()

######################################################################################################################################################
####################### Art Submission
# Status : Working but need to remake the art submition process cause Modal is trash.
######################################################################################################################################################

bot.load_extension("ArtSubmissionSystem")
	
######################################################################################################################################################
####################### Art Voting 
# Status : Working on it / not done
######################################################################################################################################################

bot.load_extension("ArtVotingSystem")

######################################################################################################################################################
####################### Code start
######################################################################################################################################################

bot.start(TOKEN) #config["token"]