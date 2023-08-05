import asyncio
import json
import shutil
from interactions import *
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

from TOKEN import TOKEN

######################################################################################################################################################
####################### MISC related code
######################################################################################################################################################

config={  
	"token":""
}  

bot = Client()

def saveConfig():
	print("save config file")
	with open("config.json", "w") as outfile:
		json.dump(config, outfile, indent=4)

def loadConfig():
		global config
		print("Loading config file")
		with open('config.json', 'r') as openfile:
			config = json.load(openfile)
		# print(f"config : {config}")

def loadData(path: str):
	with open(f'{path}/Data.json', 'r') as openfile:
		Data = json.load(openfile)
	return Data

def saveData(path: str, Data: dict[str]):
	Path(path).mkdir(parents=True, exist_ok=True)
	with open(f"{path}/Data.json", "w") as outfile:
		json.dump(Data, outfile, indent=4)
	
def checkBotConfig(guild_id):

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

def is_int(s):
    try: 
        int(s)
    except ValueError:
        return False
    else:
        return True
    
def rgb_to_hex(rgb: list):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def CheckImages(ImageURL: str, CheckColour: bool = False):
	isURLValid = False
	isFormatValid = False
	isColourValid = True
	for url in config["ValidImageURLs"]:
		if url in ImageURL:
			isURLValid = True
	if ".png" in ImageURL:
		isFormatValid = True

	if(CheckColour):
		response = requests.get(ImageURL)

		validColourList = []

		for i in range(config["ValidColourLevel"]):
			validColourList += config["ValidColour"][str(i)]

		colourList = Image.open(BytesIO(response.content)).getcolours(maxcolours=len(validColourList))

		if(colourList != None):
			for colour in colourList:

				if(rgb_to_hex(colour[1]).lower() not in [x.lower() for x in validColourList]):
					print(rgb_to_hex(colour[1]))
					isColourValid = False
		else:
			isColourValid = False
			
		return [isURLValid, isFormatValid, isColourValid]
	
	return [isURLValid, isFormatValid]

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


@listen()
async def on_startup():
	print("Bot is ready!")

	for guild in bot.guilds:
		checkBotConfig(guild.id)

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


@component_callback("ArtSuggestionButtonSubmitArt")
async def ArtValidationButton_SubmitArt_callback(ctx: ComponentContext):

	newArtSubmissionModal = Modal(
		ShortText(label="Title of your art", custom_id="ArtSubmitionTitle", required=True, placeholder="Atomium", value="Atomium"),
		ParagraphText(label="Description of your Art", custom_id="ArtSubmitionDesc", required=True, placeholder="The Atomium in pixel art.", value="The Atomium is the best monument in the world"),
		# ShortText(label="Coordinate X", custom_id="ArtSubmitionCoordinateX", required=True),
		# ShortText(label="Coordinate Y", custom_id="ArtSubmitionCoordinateY", required=True),
		ShortText(label="Link to the Big Image of your Art", custom_id="ArtSubmitionBigImageLink", required=True, value="https://media.discordapp.net/attachments/1133134231325900830/1133134231556599988/Desktop_Screenshot_2023.png"),
		ShortText(label="Link to the 1:1 scal of your Art", custom_id="ArtSubmitionScaledImagelink", required=True, value="https://media.discordapp.net/attachments/1131621964017049652/1133148822751678496/atomium.png"),
		#ShortText(label="Link to the preview od your art on the canvas", custom_id="ArtSubmitionPreviewImagelink", required=False),
		title="New Art Submission",
	)

	await ctx.send_modal(modal=newArtSubmissionModal)
	try:
		modal_ctx: ModalContext = await ctx.bot.wait_for_modal(newArtSubmissionModal, author=ctx.author, timeout=120)
	except TimeoutError:
		ctx.send("You take to much time to finish the modal, plz retry, you have 2 min.", ephemeral=True)
		return

	if( not await isArtSubbmissionValid(modal_ctx)):
		return

	ArtSuggestionEmbed = Embed(
		title = modal_ctx.responses["ArtSubmitionTitle"],
		description= modal_ctx.responses["ArtSubmitionDesc"],
		fields= [
			EmbedField(
				name="Made By :",
				value=f"{modal_ctx.author.mention}",
				inline=False
			),
			EmbedField(
				name="Coordinates",
				value="Need to be set",
				inline=False
			),
			EmbedField(
				name="Status",
				value=":orange_square: Invalid, missing information :\n\t- Coordinates",
				inline=False
			)
		],
		author=EmbedAuthor(
			name=modal_ctx.author.global_name,
			icon_url=modal_ctx.author.avatar.url
		),
		thumbnail = EmbedAttachment(
			url=modal_ctx.responses["ArtSubmitionScaledImagelink"]
		),
		images=[
			EmbedAttachment(
				url = modal_ctx.responses["ArtSubmitionBigImageLink"]
			)
		],
	)

	# download_image(modal_ctx.responses["ArtSubmitionBigImageLink"], modal_ctx.author, modal_ctx.responses["ArtSubmitionTitle"], "big")
	# download_image(modal_ctx.responses["ArtSubmitionScaledImagelink"], modal_ctx.author, modal_ctx.responses["ArtSubmitionTitle"], "scaled")
	post = await bot.get_channel(config["ArtValidationChannelId"]).create_post(name = modal_ctx.responses["ArtSubmitionTitle"], content=None, embed = ArtSuggestionEmbed) #content = f"{modal_ctx.author.mention} Your art is not valid for voting. First add the missing Information to the art submtion by clicking the button below.\nCalculate it using the [Charity](https://charity.pxls.space/) website"
	
	postEmbed = post.initial_post.embeds[0]
	postEmbed.url = "https://discord.com/channels/{ctx.guild_id}/{post.id}"
	await post.initial_post.edit(embed=postEmbed)

	await modal_ctx.send(content = f"Your suggestion is post here : https://discord.com/channels/{ctx.guild_id}/{post.id}", ephemeral=True)

	# data={  
	# 	"authorId":modal_ctx.author.id,
	# 	"name": modal_ctx.responses["ArtSubmitionTitle"],
	# 	"description": modal_ctx.responses["ArtSubmitionDesc"],
	# 	"linkBigImage": modal_ctx.responses["ArtSubmitionBigImageLink"],
	# 	"linkScaledImage":modal_ctx.responses["ArtSubmitionScaledImagelink"],
	# 	"X":None,
	# 	"Y": None
	# }

	# saveData(f'./Images/{modal_ctx.author}/{modal_ctx.responses["ArtSubmitionTitle"]}', data)

	ArtSuggestionActionRow = ActionRow(
		Button(
			style=ButtonStyle.PRIMARY,
			label="Update data",
			emoji=":identification_card:",
			custom_id="ArtSuggestionUpdateDatadButton"
		),
		Button(
			style=ButtonStyle.PRIMARY,
			label="Update images",
			emoji=":frame_with_picture:",
			custom_id="ArtSuggestionUpdateImagesButton"
		),
		Button(
			style=ButtonStyle.PRIMARY,
			label="Update coordiantes",
			emoji=":triangular_flag_on_post:",
			custom_id="ArtSuggestionUpdateCoordButton"
		)
	)

	await post.initial_post.edit(components=ArtSuggestionActionRow)

@component_callback("ArtSuggestionUpdateDatadButton")
async def art_suggestion_update_data(ctx: ComponentContext):

	initialPost = bot.get_channel(config["ArtValidationChannelId"]).get_post(ctx.message.channel.id).initial_post

	if(initialPost.embeds[0].author.name != ctx.author.global_name):
		await ctx.send(content="You aren't allowed to do this action.", ephemeral=True)
		return
	
	UpdateDataModal = Modal(
		ShortText(label="Name.", custom_id="ArtSubmitionTitle", required=True, value=initialPost.embeds[0].title),
		ShortText(label="Description.", custom_id="ArtSubmitionDesc", required=True, value=initialPost.embeds[0].description),
		title="Update data",
	)

	await ctx.send_modal(UpdateDataModal)
	try:
		modal_ctx: ModalContext = await ctx.bot.wait_for_modal(UpdateDataModal, author=ctx.author, timeout=120)
		await DisabledArtActionRow(modal_ctx.message, True)

	except TimeoutError:
		await ctx.send("You take to much time to finish the modal, plz retry, you have 2 min.", ephemeral=True)
		return

	if( not await isArtSubbmissionValid(modal_ctx)):
		await DisabledArtActionRow(ctx.message, False)
		return

	newEmbed = initialPost.embeds[0]
	newEmbed.title = modal_ctx.responses["ArtSubmitionTitle"]
	newEmbed.description = modal_ctx.responses["ArtSubmitionDesc"] 

	await initialPost.channel.edit(name=modal_ctx.responses["ArtSubmitionTitle"])

	await initialPost.edit(content=None, embed=newEmbed)

	await ctx.send("The data have been updated.", ephemeral=True)

	await DisabledArtActionRow(ctx.message, False)



@component_callback("ArtSuggestionUpdateImagesButton")
async def art_suggestion_update_images(ctx: ComponentContext):
	initialPost = ctx.channel.initial_post

	if(initialPost.embeds[0].author.name != ctx.author.global_name):
		await ctx.send(content="You aren't allowed to do this action.", ephemeral=True)
		return
	
	UpdateImagesModal = Modal(
		ShortText(label="Link to the big art.", custom_id="ArtSubmitionBigImageLink", required=True, value=initialPost.embeds[0].images[0].url),
		ShortText(label="Link to the scaled art.", custom_id="ArtSubmitionScaledImagelink", required=True, value=initialPost.embeds[0].thumbnail.url),
		title="Update images",
	)

	await ctx.send_modal(UpdateImagesModal)
	try:
		modal_ctx: ModalContext = await ctx.bot.wait_for_modal(UpdateImagesModal, author=ctx.author, timeout=120)
		await DisabledArtActionRow(modal_ctx.message, True)
	except TimeoutError:
		await ctx.send("You take to much time to finish the modal, plz retry, you have 2 min.", ephemeral=True)
		return

	if( not await isArtSubbmissionValid(modal_ctx)):
		await DisabledArtActionRow(ctx.message, False)
		return
	
	newEmbed = initialPost.embeds[0]

	newEmbed.images[0] = EmbedAttachment(
		url=modal_ctx.responses["ArtSubmitionBigImageLink"]
	)
	newEmbed.thumbnail = EmbedAttachment(
		url=modal_ctx.responses["ArtSubmitionScaledImagelink"]
	)

	await initialPost.edit(content=None, embed=newEmbed) #, components=[]

	await ctx.send("The images have been updated.", ephemeral=True)
	await DisabledArtActionRow(ctx.message, False)

@component_callback("ArtSuggestionUpdateCoordButton")
async def art_suggestion_update_coord(ctx: ComponentContext):

	initialPost = ctx.channel.initial_post

	if(initialPost.embeds[0].author.name != ctx.author.global_name):
		await ctx.send(content="You aren't allowed to do this action.", ephemeral=True)
		return

	coord = art_suggestion_get_coord(ctx.message)
	if(coord == None):
		x = y = ""
	else:
		x = str(coord[0])
		y = str(coord[1])

	UpdateCoordModal = Modal(
		ShortText(label="Coordinate X", custom_id="ArtSubmitionCoordinateX", required=True, value=x),
		ShortText(label="Coordinate Y", custom_id="ArtSubmitionCoordinateY", required=True, value=y),
		ShortText(label="Link to the preview of your art on the canvas", custom_id="ArtSubmitionPreviewImagelink", required=True, value="https://media.discordapp.net/attachments/1131621964017049652/1133150932977319956/image.png"),
		title="Update coordinates",
	)

	await ctx.send_modal(UpdateCoordModal)
	try:
		modal_ctx: ModalContext = await ctx.bot.wait_for_modal(UpdateCoordModal, author=ctx.author, timeout=120)
		await DisabledArtActionRow(modal_ctx.message, True)
	except TimeoutError:
		await ctx.send("You take to much time to finish the modal, plz retry, you have 2 min.", ephemeral=True)
		return

	if( not await isArtSubbmissionValid(modal_ctx)):
		await DisabledArtActionRow(ctx.message, False)
		return

	newEmbed = initialPost.embeds[0]
	newEmbed.fields[1] = EmbedField(
			name="Coordinates :",
			value=f"X : {modal_ctx.responses['ArtSubmitionCoordinateX']}, Y : {modal_ctx.responses['ArtSubmitionCoordinateY']}",
			inline = False
		)
	newEmbed.images = [
		EmbedAttachment(
			url=newEmbed.images[0].url
		),
		EmbedAttachment(
			url=modal_ctx.responses["ArtSubmitionPreviewImagelink"]
		)
	]

	await initialPost.edit(content=None, embed=newEmbed) #, components=[]

	await ctx.send("The Coordinates have been updated.", ephemeral=True)
	await DisabledArtActionRow(ctx.message, False)

async def isArtSubbmissionValid(ctx: ModalContext) -> bool: #, post: GuildForumPost
	isArtValid = True
	modalErrorEmbed = Embed(
		title="ERROR",
		color=[255,0,0],
		description="Error occure during the submition of your art :"
	)

	#first checking the name to see if it match everywhere - pass

	#checking the images.
	try:
		isBigImageURLValid, isBigImageFormatValid = CheckImages(ctx.responses["ArtSubmitionBigImageLink"])
		isScaledImageURLValid, isScaledImageFormatValid, isScaledImageColourValid = CheckImages(ctx.responses["ArtSubmitionScaledImagelink"], True)

		if(not isBigImageFormatValid or not isBigImageURLValid):
			errorMessage = ""
			if(not isBigImageURLValid):
				errorMessage += "- The link to the image is wrong.\n"
			if(not isBigImageFormatValid):
				errorMessage += "- The format of the image is wrong."
			
			isArtValid = False

			modalErrorEmbed.add_field(
				name="Big image error:",
				value=errorMessage,
				inline=False
			)	

		if(not isScaledImageFormatValid or not isScaledImageURLValid or not isScaledImageColourValid):
			errorMessage = ""
			if(not isScaledImageURLValid):
				errorMessage += "- The link to the image is wrong.\n"
			if(not isScaledImageFormatValid):
				errorMessage += "- The format of the image is wrong.\n"
			if(not isScaledImageColourValid):
				errorMessage += "- The colour used in the image isn't available on the R/Place."
			
			isArtValid = False

			modalErrorEmbed.add_field(
				name="Scaled image error:",
				value=errorMessage,
				inline=False
			)
	except:
		None

	#checking the coord :
	try:
		isPreviewImageURLValid, isPreviewImageFormatValid = CheckImages(ctx.responses["ArtSubmitionPreviewImagelink"])
		isCoordXValid = is_int(ctx.responses["ArtSubmitionCoordinateX"])
		isCoordYValid = is_int(ctx.responses["ArtSubmitionCoordinateY"])

		if(not isCoordXValid or not isCoordYValid):
			errorMessage = ""
			if(not isCoordXValid):
				errorMessage += "- The X Coordinate is wrong.\n"
			if(not isCoordYValid):
				errorMessage += "- The Y Coordinate is wrong."

			modalErrorEmbed.add_field(
				name="Coordinates error:",
				value=errorMessage,
				inline=False
			)
			isArtValid = False

		if(not isPreviewImageURLValid or not isPreviewImageFormatValid):
			errorMessage = ""
			if(not isPreviewImageURLValid):
				errorMessage += "- The link to the image is wrong.\n"
			if(not isPreviewImageFormatValid):
				errorMessage += "- The format of the image is wrong."
			
			modalErrorEmbed.add_field(
				name="Preview image error:",
				value=errorMessage,
				inline=False
			)
			isArtValid = False
	except :
		# coord = art_suggestion_get_coord(ctx.message)
		# if(coord == None):
		# 	isFirstValidation = True
		None

	if(not isArtValid):
		await ctx.send(embed=modalErrorEmbed, ephemeral=True)
		return False
	
	newEmbed = ctx.message.embeds[0]

	try:
		boool = ":orange_square:" in newEmbed.fields[2].value or ":green_square:" in newEmbed.fields[2].value
	except:
		boool = False

	if(boool):
		newEmbed.fields[2] = EmbedField(
				name="Status",
				value=":green_square: Valid",
				inline=False
			)
		await ctx.message.edit(content=None, context=ctx, embed=newEmbed)

		await ctx.message.clear_all_reactions()

		for react in [":white_check_mark:", ":x:"]:
			await ctx.message.add_reaction(react)

	return True
	

	# if(post.name != post.initial_post.embeds[0].title or post.name)

	
@message_context_menu(name="Invalid art suggestion")
async def InvalidArtSuggestion(ctx: ContextMenuContext):

	if(not ctx.author.has_role(bot.get_guild(ctx.guild_id).get_role(config["PlaceModoRole"]))):
		await ctx.send("You don't have the permission to do this action.", ephemeral=True)
		return

	if(ctx.channel.parent_channel.type != ChannelType.GUILD_FORUM or ctx.channel.type != ChannelType.GUILD_PUBLIC_THREAD or ctx.channel.parent_channel.id != config["ArtValidationChannelId"]):
		await ctx.send("Plz, use this app in an art suggestion post.", ephemeral=True)
		return

	InvalidArtEmbed = Embed(
		title="Invalid this Art",
		description="Why this art should be invalidate ?",
		color="#FF4500"
	)

	InvalidArtStringSelectMenu = StringSelectMenu(
		StringSelectOption(
			label="Wrong data",
			description="select if the date is wrong (Name, Description)",
			emoji=":identification_card:",
			value="InvalidData"
		),
		StringSelectOption(
			label="The big image is wrong",
			description="Select if the big image is wrong.",
			emoji=":identification_card:",
			value="InvalidBigImage"
		),
		max_values=2
	)

	await ctx.send(embed=InvalidArtEmbed, components=InvalidArtStringSelectMenu, ephemeral=True)

	try:
		used_component = await bot.wait_for_component(components=InvalidArtStringSelectMenu, timeout=120)
	except TimeoutError:
		await ctx.send("You take to much time to finish, plz retry, you have 2 min.", ephemeral=True)
		return

	strSlectMenu_ctx = used_component.ctx

	await strSlectMenu_ctx.message.delete(context=ctx)

	newStatuString = ":red_square: Invalidate by modo, Infomration(s) to change :"

	for issue in strSlectMenu_ctx.values:
		match issue:
			case 'InvalidData' :
				newStatuString += "\n- The data is invalid."
			case 'InvalidBigImage':
				newStatuString += "\n- The big image is invalid."
			case _:
				newStatuString += "\n- Other issues."
		
	initial_post = ctx.channel.initial_post
	newEmbed = initial_post.embeds[0]
	newEmbed.fields[2].value = newStatuString
	await initial_post.edit(embed=newEmbed)

	await initial_post.clear_all_reactions()

	await ctx.send(content="The art have been Invalidate", ephemeral=True)
	
######################################################################################################################################################
####################### Art Voting 
# Status : Working on it / not done
######################################################################################################################################################

project = SlashCommand(name="project", description="All project commands")

@project.subcommand(
	# group_name="set",
	# group_description="Set the value of ...",
	sub_cmd_name="is-done", 
	sub_cmd_description="The current project is done.",
	options= [
		{
			"name": "newvote",
			"description": "k",
			"type": 5,
			"required": "false"
		}
	]
)
async def projectIsDone(ctx: SlashContext, newvote):
	await ctx.send("Yes")

	if(newvote):
		await ctx.send("heelo")
		artSuggestionChannel = bot.get_channel(config["ArtValidationChannelId"])
		posts = artSuggestionChannel.get_posts(exclude_archived=True)
		for post in posts:
			print(post)
			print(await post.fetch_messages()) #use this to load the message inside the post or the post.initial_post return None
			try:
				if(":green_square:" in post.initial_post.embeds[0].fields[2].value):
					print(reactions = post.initial_post.reactions)
			except:
				print(post.initial_post)
			
		


######################################################################################################################################################
####################### Code start
######################################################################################################################################################

loadConfig()

bot.start(TOKEN) #config["token"]