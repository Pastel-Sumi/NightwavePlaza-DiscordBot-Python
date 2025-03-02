import os
import asyncio
import requests

#Discord related imports
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice
from dotenv import load_dotenv

#Youtube import
import yt_dlp as youtube_dl

FFMPEG_PATH = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

BOT =  commands.Bot(command_prefix="!", intents=intents)
#client = MyClient(intents=intents)

#Queues
queues = {}

@BOT.event
async def on_ready():
    await BOT.wait_until_ready()
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} commands(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

#Function to play the next song in the queue
def play_next(vc):
    # If there are songs in the queue
    if queues[vc.guild.id]:
        next_url, title = queues[vc.guild.id].pop(0)
        ffmpeg_options = {'options': '-vn'}
        vc.play(discord.FFmpegPCMAudio(next_url, **ffmpeg_options), after=lambda e:play_next(vc))
        print(f"Now playing: {title}")
    else:
        asyncio.run_coroutine_threadsafe(vc.disconnect(), BOT.loop)

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
        await interaction.response.send_message("You need to be in a voice channel, dummy!")
        return
    
    channel = author.voice.channel
    vc = interaction.guild.voice_client

    if interaction.guild.id not in queues:
        queues[interaction.guild.id] = []

    #Youtube download options
    ydl_opts = {'format': 'bestaudio/best', 'extractaudio': True, 'audioformat': 'mp3', 'outtmpl': 'song.%(ext)s', 'quiet': True}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        url = info['url']
        title = info.get('title', 'Unknown Title')

    if vc and vc.is_playing():
        queues[interaction.guild.id].append((url, title))
        await interaction.response.send_message(f" **{title}** added to queue.")
    else:
        if not vc:
            print("Connecting to voicechat...")
            vc = await channel.connect()
        
        queues[interaction.guild.id].append((url, title))
        play_next(vc) 

        await interaction.response.send_message(f"Playing: {info['title']}")

@BOT.tree.command(name="skip", description="Skips the current song")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("Skipping song...")
    else:
        await interaction.response.send_message("There is no song playing.")

@BOT.tree.command(name="queue", description="Shows the current song queue")
async def show_queue(interaction: discord.Interaction):
    if interaction.guild.id not in queues or not queues[interaction.guild.id]:
        await interaction.response.send_message("The queue is empty.")
    else:
        queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(queues[interaction.guild.id])])
        await interaction.response.send_message(f" **Current queue:** \n {queue_list}")

@BOT.tree.command(name="stop", description="Stops the bot and clears the queue")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message(" Stopped playback and cleared the queue")
    else:
        await interaction.response.send_message("I'm not in a voice channel, dummy.")

BOT.run(TOKEN)