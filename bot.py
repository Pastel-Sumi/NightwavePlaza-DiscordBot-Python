import os
import asyncio
import requests

#Discord related imports
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

BOT =  commands.Bot(command_prefix="!", intents=intents)
#client = MyClient(intents=intents)


@BOT.event
async def on_ready():
    await BOT.wait_until_ready()
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} commands(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@BOT.tree.command(name="help", description="Give a list of available commands")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("* `/play [link]`:\n"+
                                            "   * Plays a youtube `link` in voice chat.\n"+
                                            "* `/radio`: \n"+
                                            "   * Joins voice channel and connects to the Nightwave Plaza radio.\n"+
                                            "* `/help`:\n"+
                                            "   * Shows the user a list of all of this bot's commands.",
                                            ephemeral=True)

@BOT.tree.command(name="play", description="Plays a song from youtube")
async def play(interaction: discord.Interaction ,link: str):
    author = interaction.user #The user who called the command
    if author.voice is None or author.voice.channel is None:
        await interaction.response.send_message("You need to be in a voice channel, dummy")
        return
    channel = author.voice.channel
    if interaction.guild.voice_client:
        vc = interaction.guild.voice_client
    else:
        print("Connecting to voicechat...")
        vc =await channel.connect()

BOT.run(TOKEN)