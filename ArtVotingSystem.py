from interactions import *

from utils import config

class ArtVotingSystem(Extension):
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
    async def projectIsDone(self, ctx: SlashContext, newvote: bool = False):
        await ctx.send("Yes")
        if(newvote):
            positif_react_count = 0
            negatif_react_count = 0
            artArrayForVote = []
            await ctx.send("heelo")
            artSuggestionChannel = self.bot.get_channel(config["ArtValidationChannelId"])
            posts = artSuggestionChannel.get_posts(exclude_archived=True)
            for post in posts:
                initial_post = await post.fetch_message(post.id) #The id of the initial message is the same as the post
                try:
                    if(":green_square:" in initial_post.embeds[0].fields[2].value):
                        reactions = initial_post.reactions
                        for react in reactions:
                            if(react.emoji.name == "✅"):
                                positif_react_count = react.count
                                print(react.count)
                            elif(react.emoji.name == "❌"):
                                negatif_react_count = react.count
                                print(react.count)
                        
                        ratio = positif_react_count - negatif_react_count


                except:
                    print(post.initial_post)

def setup(bot):
    ArtVotingSystem(bot)