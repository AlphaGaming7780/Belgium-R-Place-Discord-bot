import json
import os

import requests
from utils import config, loadConfig, art_suggestion_get_coord
from interactions import *
from github import *
from github import GitRef
from TOKEN import GITHUB_TOKEN
from datetime import datetime

defaultTemplatesConfig = {
    "faction": "/r/belgium",
    "contact": "https://discord.gg/Belgium",
    "templates": [
        {
            "name": "TEST",
            "sources": [
                ""
            ],
            "x": 0,
            "y": 0
        }
    ],
    "whitelist": [],
    "blacklist": []
}

template = {
    "name": "",
    "sources": [
        ""
    ],
    "x": 0,
    "y": 0
},

config = loadConfig()
githubTemplateRepo = None
path = os.path.dirname(os.path.realpath(__file__))

def GitSetup():
    global localTemplateRepo, githubTemplateRepo
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    githubTemplateRepo = g.get_user().get_repo(config["TemplateGithubRepoName"])
    # for event in g.get_user().get_events():
    #     print(f"repo : {event.repo.name}\nType : {event.type}")

def UploadAnArt(message: Message, author: str): 

    if(githubTemplateRepo != None):

        sb = githubTemplateRepo.get_branch("main")
        newBranch = githubTemplateRepo.create_git_ref(ref=f"refs/heads/{message.embeds[0].title}_{author}", sha=sb.commit.sha)

        r = requests.get(message.embeds[0].thumbnail.url, stream=True)
        if r.status_code == 200:
            imageName = getValidName(f"/Images/RPlace/Belgian/{message.embeds[0].title}/{author}/", imageName)
            UpdateTheTemplate(message.embeds[0].title, author, art_suggestion_get_coord(message), imageName, newBranch)
            #githubTemplateRepo.create_file(path=f"/Images/RPlace/Belgian/{message.embeds[0].title}/{author}/{imageName}.png", content=r.content, branch=f"{message.embeds[0].title}_{author}", message="OOHHH YEEEAAAAHHHH")
            print("YESS")
        else:
            print("ERROR: Failed to get the image.")
    else:
        print("ERROR: githubTemplateRepo = NONE")

def UpdateTheTemplate(title: str, author: str, coord: list[int], imageName: str, newBranch: GitRef.GitRef):
    templateConfig = dict(json.loads(githubTemplateRepo.get_contents("Belgium RPlace Template.json").decoded_content.decode().replace("'", '"')))
    templates = list(templateConfig["templates"])
    template["name"] = f"{title} | Made by {author}"
    template["sources"][0] = f"{newBranch.url}/Images/RPlace/Belgian/{title}/{author}/{imageName}.png"
    template["x"] = coord[0]
    template["y"] = coord[1]
    templates.insert(0, template)
    print(template)
    print(templates)

def getValidName(path: str):
    imageName = None
    contents = githubTemplateRepo.get_contents(path)

    for file in contents:
        file.na

    return imageName