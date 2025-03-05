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
        asyncio.create_task(disconnect_after_timeout(vc))
        #asyncio.run_coroutine_threadsafe(vc.disconnect(), BOT.loop)

#Bot disconnects after 5 minutes of no music
async def disconnect_after_timeout(vc, timeout=300):
    await asyncio.sleep(timeout)
    if not vc.is_playing() and len(queues.get(vc.guild.id, [])) == 0:
        await vc.disconnect()

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
    await interaction.response.defer() #To avoid timeout

    author = interaction.user #The user who called the command
    if author.voice is None or author.voice.channel is None:
        await interaction.followup.send("You need to be in a voice channel, dummy!")
        return
    
    channel = author.voice.channel
    vc = interaction.guild.voice_client

    if interaction.guild.id not in queues:
        queues[interaction.guild.id] = []

    #Youtube download options
    #ydl_opts = {'format': 'bestaudio/best', 'extractaudio': True, 'audioformat': 'mp3', 'outtmpl': 'song.%(ext)s', 'quiet': True}
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        url = info['url']
        title = info.get('title', 'Unknown Title')

    if vc and vc.is_playing():
        queues[interaction.guild.id].append((url, title))
        await interaction.followup.send(f" **{title}** added to queue.")
    else:
        if not vc:
            print("Connecting to voicechat...")
            vc = await channel.connect()
        
        queues[interaction.guild.id].append((url, title))
        play_next(vc) 

        await interaction.followup.send(f"Playing: {info['title']}")

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
    await interaction.response.defer()

    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        vc.stop()
        await vc.disconnect()
        await interaction.followup.send(" Stopped playback and cleared the queue")
    else:
        await interaction.followup.send("I'm not in a voice channel, dummy.")


#Radio
@BOT.tree.command(name="radio", description="Joins voice channel and connects to Nightwave Plaza")
async def radio(interaction: discord.Interaction):
    await interaction.response.defer() #To avoid timeout

    author = interaction.user
    if author.voice is None or author.voice.channel is None:
        await interaction.followup.send("You need to be in a voice channel, dummy!")
        return
    channel = author.voice.channel
    vc = interaction.guild.voice_client

    #NIGHTWAVE PLAZA URL
    RADIO_URL = "https://radio.plaza.one/mp3"

    #Clear queue before playing radio
    queues[interaction.guild.id] = []

    if vc and vc.is_playing():
        vc.stop()
    
    if not vc:
        vc = await channel.connect()
    
    #Radio stream
    ffmpeg_options = {"options": "-vn"}
    vc.play(discord.FFmpegPCMAudio(RADIO_URL, **ffmpeg_options))

    await interaction.followup.send("📻 Now playing: **Nightwave Plaza** 🎶")

@BOT.tree.command(name="stopradio", description="Stops the radio stream and disconnects the bot")
async def stopradio(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_connected():
        await vc.disconnect()
        await interaction.response.send_message("Radio stream stopped and disconnected. Not A E S T H E T I C")
    else:
        await interaction.response.send_message("I'm not connected to a voice channel, dummy.")

BOT.run(TOKEN)