import asyncio
from interactions import *
from GitManager import UploadAnArt

from utils import config, get_id_using_mention

voteReactOption = [
	":one:",
	":two:",
	":three:",
	":four:",
	":five:",
	":six:",
	":seven:",
	":eight:",
	":nine:",
	":zero:"
]

class ProjectVotingSystem(Extension):
	project = SlashCommand(name="project", description="All project commands")

	@project.subcommand(
		# group_name="set",
		# group_description="Set the value of ...",
		sub_cmd_name="is-done", 
		sub_cmd_description="The current project is done.",
		options= [
			{
				"name": "newvote",
				"description": "test", #Do we make a new vote for the next project to do, it would be add to the project queue or would be the current project | by default is `True`
				"type": 5,
				"required": "false"
			}
		]
	)
	async def projectIsDone(self, ctx: SlashContext, newvote: bool = True):
		await ctx.send("the current project is done")
		# make an anoncement to tell poeple we go to the next art
		# make a project queue
		if(newvote):
			await self.NewProjectVote(ctx)

	
	@project.subcommand(
		# group_name="set",
		# group_description="Set the value of ...",
		sub_cmd_name="new-vote", 
		sub_cmd_description="Create a vote for a new project."
	)
	async def NewProjectVote(self, ctx: SlashContext):
		positif_react_count = 0
		negatif_react_count = 0
		artArrayForVote = []
		await ctx.send("A vote for the new art project is going to be ")
		artSubmissionChannel = self.bot.get_channel(config["ArtSubmissionChannelId"])
		posts = artSubmissionChannel.get_posts(exclude_archived=True)
		for post in posts:
			initial_post = await post.fetch_message(post.id) #The id of the initial message is the same as the post
			try:
				if(":green_square:" in initial_post.embeds[0].fields[2].value):
					reactions = initial_post.reactions
					for react in reactions:
						if(react.emoji.name == "✅"):
							positif_react_count = react.count
						elif(react.emoji.name == "❌"):
							negatif_react_count = react.count
					
					ratio = positif_react_count - negatif_react_count
					if(len(artArrayForVote) == 0):
						artArrayForVote.insert(0, [post.id, ratio])
					else:
						idx = 0
						for art in artArrayForVote:
							if(art[1] < ratio):
								print(post.name)
								artArrayForVote.insert(idx, [post.id, ratio])
								break
							idx += 1
						
						artArrayForVote.append([post.id, ratio])

			except:
				print(f"failed : {post.name}")

		print(artArrayForVote)
		if(len(artArrayForVote) < config["MinArtNeededToMakeAVote"]):
			await ctx.send(content=f"No enough art to make a vote, the minimum needed is {config['MinArtNeededToMakeAVote']}.")
			return
		
		content = f"{ctx.bot.get_guild(ctx.guild_id).get_role(config['PlaceRole']).mention} A new art vote, plz vote for the art you want to make by reacting to this message."
		embeds = []
		for idx in range(config['MinArtNeededToMakeAVote']):
			post = ctx.bot.get_channel(config['ArtSubmissionChannelId']).get_post(artArrayForVote[idx][0])
			await post.edit(locked=True, archived=True)
			embed = post.initial_post.embeds[0]
			embeds.append(
				Embed(
					title=embed.title,
					description=embed.description,
					thumbnail=embed.thumbnail,
					fields=[embed.fields[0], embed.fields[1]],
					images=embed.images,
					author=embed.author
				)
			)
			content += f"\n\t{voteReactOption[idx]}) {embed.title} Made by {embed.fields[0].value}"	
		
		voteMessage = await ctx.bot.get_channel(config['ArtVotingChannelId']).send(content=content, embeds=embeds)
		for idx in range(config['MinArtNeededToMakeAVote']):
			await voteMessage.add_reaction(voteReactOption[idx])

		await asyncio.sleep(10) # 10 min <- maybe change that. FOR NOW 10 SEC

		#TO-DO make the annonce in the announce chanel
		#self.bot.get_channel(config[""]).send()

		reactions = voteMessage.reactions
		idx = 0
		mostVotedArtIdx = 0
		mostVotedArtCount = 0
		for react in reactions:
			if mostVotedArtCount < react.count:
				mostVotedArtCount = react.count
				mostVotedArtIdx = idx
			idx += 1
		
		for idx in range(config['MinArtNeededToMakeAVote']):
			if idx != mostVotedArtIdx:
				post = ctx.bot.get_channel(config['ArtSubmissionChannelId']).get_post(artArrayForVote[idx][0])
				await post.edit(locked=False, archived=False)
			else:
				winingArtMessage = ctx.bot.get_channel(config['ArtSubmissionChannelId']).get_post(artArrayForVote[idx][0]).initial_post

		UploadAnArt(message=winingArtMessage, author=self.bot.get_member(get_id_using_mention(winingArtMessage.embeds[0].fields[0].value), ctx.guild_id).global_name)


			
def setup(bot):
	ProjectVotingSystem(bot)