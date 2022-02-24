#Tested on Python 3.9.2
import discord
from discord import channel, message, FFmpegPCMAudio
from discord.ext import commands
import youtube_dl
from youtube_dl import YoutubeDL
from youtube_dl.extractor import get_info_extractor
from youtube_dl.postprocessor import ffmpeg
import asyncio
import urllib.parse, urllib.request, re

client = commands.Bot(command_prefix="-", help_command=None)
###PUT TOKEN HERE###
TOKEN = str(input("Enter bot's token: "))
###PUT TOKEN HERE###

total_duration = [0]
sources = {} #for player
queues = {} #just songs' name output to discord
author = ['']#user's name that requests songs 
current_song = ['']
played_songs = ['']
user_command = """1.play\n2.pause\n3.resume\n4.skip\n5.stop\n6.leave\n7.list\n8.played\n9.join\nExample: -play leave the door open\n"""

ydl_opts = {'format' : 'bestaudio', 'noplaylist' : 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def get_played_song():
        text = ''
        if played_songs[0] != '':
                count = 1
                for item in played_songs[0]:
                        text += str(count) + '. ' + item + '\n'
                        count += 1
        else:
                text += 'ไม่มีเพลงถูกเล่น'
        return text

def get_song_info(url):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                #Can get song's information here such as: name, id, duration
                info = ydl.extract_info(url, download=False) 
        return info

def get_youtube_link(name : str):
        qury_string = urllib.parse.urlencode({'search_query': name})
        htm_content = urllib.request.urlopen('http://www.youtube.com/results?' + qury_string)
        #array of songs' url but we need the first one
        search_result = re.findall('/watch\\?v=(.{11})', htm_content.read().decode())
        
        return "https://www.youtube.com/watch?v=" + search_result[0]


@client.command()
async def join(ctx):
        if ctx.voice_client:
                print("bot has already joined")
                return
        guild_id = ctx.message.guild.id
        song_stamp = ['']

        voice_client = discord.utils.get(client.voice_clients, guild = ctx.guild)
        
        #Is author that summon bot on voice channel
        if ctx.author.voice:
                channel = ctx.message.author.voice.channel
                if not ctx.voice_client:
                        await channel.connect()
                        await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)
                        # joined[0] = 1
                        
                        await ctx.send("ฅ^•ﻌ•^ฅ.  .  . ~ . ~")
                        await ctx.send("หวัดดีงับบ. . . พร้อมเปิดเพลงแน้วว !")
                        
                        embed = discord.Embed(colour = discord.Colour.green())
                        embed.add_field(name= "คำสั่งทั้งหมด", value= user_command, inline= False)
                        await ctx.send(embed=embed)

                        voice_client = discord.utils.get(client.voice_clients, guild = ctx.guild)

        # every second automatically check and output current song's name to the discord
        # I use this method instead of using lambda in player. It'll crashs when we have more than 8 songs in queues                
        while ctx.voice_client:
                if guild_id in sources:
                        if sources[guild_id] != []:
                                if not voice_client.is_playing() and voice_client.is_paused() == 0:
                                        player(ctx, guild_id)

                #check if song_stamp is the playing song
                if song_stamp[0] != current_song[0] and current_song[0] != '':
                        next_song = ['']
                        if guild_id in queues:        
                                if queues[guild_id] != []: 
                                        next_song[0] = queues[guild_id][0]
                                else:
                                        next_song[0] = "-"
                        else:
                                next_song[0] = "-"

                        song_url = get_youtube_link(current_song[0])
                        info = get_song_info(song_url)
                        duration_info = info['duration']
                        song_duration = str(duration_info // 60) + ':' + (str(duration_info % 60).zfill(2))
                        total_duration[0] += int(duration_info)

                        embed = discord.Embed(colour = discord.Colour.red())
                        embed.set_author(name= current_song[0])
                        embed.add_field(name= song_url, value="ระยะเวลา : " + str(song_duration) , inline=False)
                        embed.add_field(name="เปิดโดย  :  ", value= author[0][0]) 
                        embed.add_field(name="เพลงถัดไป  :  ", value= next_song[0])
                        embed.set_image(url= info['thumbnail'])
                        
                        await ctx.send(embed=embed)

                        song_stamp[0] = current_song[0]
                        author[0].pop(0)

                #if current song is empty
                elif song_stamp[0] != '' and current_song[0] == '' and ctx.voice_client:
                        song_stamp[0] = ''

                        embed = discord.Embed(colour = discord.Colour.dark_red())
                        embed.set_author(name= "ไม่มีเพลงเล่นต่อ")
                        await ctx.send(embed=embed)

                await asyncio.sleep(1)
                
def player(ctx, guild_id):
        if guild_id in sources:
                if sources[guild_id] != []:
                        voice_client = discord.utils.get(client.voice_clients, guild = ctx.guild)

                        if played_songs[0] == '':
                                played_songs[0] = [queues[guild_id][0]]
                        else:
                                played_songs[0].append(queues[guild_id][0])
                        
                        current_song[0] = queues[guild_id].pop(0)
                        URL = sources[guild_id].pop(0)

                        voice_client.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
                else:
                        current_song[0] = ''
                        print("Ran Out of Song")

def get_queue_list(guild_id):
        text = ""
        if guild_id in queues:
                count = 1
                for item in queues[guild_id]:
                        text += str(count) + '.' + item + '\n'
                        count += 1
        return text

@client.event
async def on_ready():
        print("Ready to go...")
        print(user_command)

@client.command()
async def help(ctx):
        embed = discord.Embed(colour = discord.Colour.green())
        embed.add_field(name= "คำสั่งทั้งหมด", value= user_command, inline= False)
        await ctx.send(embed=embed)   

@client.command()
async def play(ctx, * , search : str):
        guild_id = ctx.message.guild.id
        url = ['']
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)

        if ctx.author.voice:
                if not ctx.voice_client:
                        await ctx.send('ಇ/ᐠ ̥ᵔ  ̮  ᵔ ̥ ᐟ\ಇ')
                        await ctx.send("พิมพ์ -join ให้เหมียวเข้าห้องก่อนน๊าา")
                        return

        if "youtube." in search or "youtu.be" in search:
                url[0] = search
        else:
                url[0] = get_youtube_link(search)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                song_info = ydl.extract_info(url[0], download=False) #get songs' information here such as: name, id, duration
        
        playable_url = song_info['formats'][0]['url']

        if guild_id in sources:
                sources[guild_id].append(playable_url)
                queues[guild_id].append(song_info['title'])

                author[0].append(str(ctx.author.name))

                if voice.is_playing() or voice.is_paused():
                        embed = discord.Embed(colour = discord.Colour.dark_blue())
                        embed.add_field(name= "เพลงที่รอเล่น", value= get_queue_list(guild_id), inline= False)
                        await ctx.send(embed=embed)
        else:
                sources[guild_id] = [playable_url]
                queues[guild_id] = [ song_info['title'] ]
                
                author[0] = [str(ctx.author.name)]
                

@client.command()
async def leave(ctx):
        if ctx.voice_client:
                guild_id = ctx.message.guild.id
                if guild_id in queues:
                        queues[guild_id].clear()
                        sources[guild_id].clear()

                current_song[0] = ''
                await ctx.guild.voice_client.disconnect()      

                min = int(total_duration[0] // 60)
                sec = int(format(total_duration[0]% 60).zfill(2))
                embed = discord.Embed(colour = discord.Colour.purple())
                embed.add_field(name= "เพลงที่ถูกเล่นทั้งหมด", value= get_played_song(), inline= False)
                embed.add_field(name= "รวมเวลาทั้งหมด", value= (f"{str(min)}:{str(sec)} นาที"), inline= False)
                await ctx.send(embed=embed)

                await ctx.send('/ᐠ ̥  ̮  ̥ ᐟ\ฅ     ไปแล้วน๊าา. . . ')

        else:    
                await ctx.send("~ ยังไม่ได้เข้าห้องเยยง่ะ. . .(´°̥̥̥̥̥̥̥̥ω°̥̥̥̥̥̥̥̥｀)")


@client.command(pass_context = True)
async def pause(ctx):
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        if voice.is_playing():
                voice.pause()
                embed = discord.Embed(colour = discord.Colour.dark_grey())
                embed.add_field(name= "/ᐠ – .–ᐟ\  z Z Z", value= "Paused", inline= False)
                await ctx.send(embed=embed)
        else:
                await ctx.send("เพลงหยุดอยู่ง่ะ")

@client.command()
async def resume(ctx):
        voice =  discord.utils.get(client.voice_clients, guild = ctx.guild)
        embed = discord.Embed(colour = discord.Colour.green())
        if voice.is_paused():
                voice.resume()
                embed.add_field(name= "เล่นเพลงต่อ", value= current_song[0], inline= False)
                await ctx.send(embed=embed)
        elif voice.is_playing():
                embed.add_field(name= "∩(・ω・)∩", value= "เพลงกำลังเล่นอยู่", inline= False)
                await ctx.send(embed=embed)
        else:
                embed.add_field(name= "∩(・ω・)∩", value= "ไม่มีเพลงเล่นอยู่", inline= False)
                await ctx.send(embed=embed)

@client.command()
async def stop(ctx):
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        embed = discord.Embed(colour = discord.Colour.dark_teal())
        if voice.is_playing() or voice.is_paused():
                guild_id = ctx.message.guild.id
                if guild_id in queues:
                        queues[guild_id].clear()
                        sources[guild_id].clear()
                current_song[0] = ''
                

                voice.stop()
                embed.add_field(name= " /ᐠo  oᐟ\ ɴʏᴀ~", value= "หยุดเล่น.  .  .", inline= False)
                await ctx.send(embed=embed)
        else:
                embed.add_field(name= "(ﾐゝᆽ･ﾐ)", value= "เพลงไม่ได้เล่นอยู่แล้ว. . .", inline= False)
                await ctx.send(embed=embed)
                
@client.command()
async def skip(ctx):
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        embed = discord.Embed(colour = discord.Colour.blurple())
        if voice.is_playing() or voice.is_paused():
                voice.stop()
                
                embed.add_field(name= "/ᐠ ̥    ̣̮ ̥ ᐟ\ﾉ ~", value= "Skip ~", inline= False)
                await ctx.send(embed=embed)
        else:
                embed.add_field(name= "/ᐠ=ᆽ≠ ᐟ \∫", value= "ไม่มีเพลงให้ Skip แล้วง่ะ. . . ~", inline= False)
                await ctx.send(embed=embed)
        
@client.command()
async def list(ctx):
        guild_id = ctx.message.guild.id
        embed = discord.Embed(colour = discord.Colour.dark_blue())
        if guild_id in queues and queues[guild_id] != []:
                embed.add_field(name= "เพลงที่รอเล่น", value= get_queue_list(guild_id), inline= False)
                await ctx.send(embed=embed)
        else:
                embed.add_field(name= "(╯°□°）╯", value= "ไม่มีเพลงในคิว", inline= False)
                await ctx.send(embed=embed)
                
@client.command()
async def played(ctx):
        min = int(total_duration[0] // 60)
        sec = int(format(total_duration[0]% 60).zfill(2))
        embed = discord.Embed(colour = discord.Colour.purple())
        embed.add_field(name= "เพลงที่ถูกเล่นทั้งหมด", value= get_played_song(), inline= False)
        embed.add_field(name= "รวมเวลาทั้งหมด", value= (f"{str(min)}:{str(sec)} นาที"), inline= False)
        await ctx.send(embed=embed)

client.run(TOKEN)