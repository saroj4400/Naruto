from __future__ import unicode_literals
import os
import requests
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch

@Client.on_message(filters.command(['song', 'mp3']) & filters.private)
async def song(client, message):
    user_id = message.from_user.id 
    user_name = message.from_user.first_name 
    query = ' '.join(message.command[1:])
    m = await message.reply(f"**Searching your song...**\n {query}")
    
    # Define options for yt-dlp
    ydl_opts = {
        "format": "bestaudio[ext=mp3]",
        "outtmpl": "%(title)s.%(ext)s",  # Set the output template
        "quiet": True  # Avoid verbose output
    }
    
    try:
        # Search for the song using YouTubeSearch
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"]
        thumbnail = results[0]["thumbnails"][0]

        # Download the thumbnail
        thumb_name = f'thumb_{title}.jpg'
        thumb = requests.get(thumbnail, allow_redirects=True)
        with open(thumb_name, 'wb') as f:
            f.write(thumb.content)

        # Download the song using yt-dlp
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict)
        
        # Send the song to the user
        cap = f"**Song Title:** {title}\n**Requested by:** {message.from_user.first_name}"
        await message.reply_audio(
            audio_file,
            caption=cap,
            thumb=thumb_name
        )
        
        # Clean up the temporary files
        os.remove(audio_file)
        os.remove(thumb_name)
        await m.delete()

    except Exception as e:
        await m.edit("**Error:** Unable to download the song. Please try again later.")
        print(str(e))


@Client.on_message(filters.command(["video", "mp4"]))
async def vsong(client, message):
    query = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None
    if not query:
        return await message.reply("Example: /video Your video query")

    m = await message.reply(f"**Searching for your video...** `{query}`")
    
    # Search for the video using yt-dlp
    ydl_opts = {
        "format": "best",
        "outtmpl": "%(id)s.%(ext)s",  # Set the output template
        "quiet": True  # Avoid verbose output
    }

    try:
        search = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{search[0]['url_suffix']}"
        video_title = search[0]["title"]
        video_thumbnail = search[0]["thumbnails"][0]

        # Download the video
        with YoutubeDL(ydl_opts) as ydl:
            ydl_data = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(ydl_data)
        
        # Send the video to the user
        cap = f"**Video Title:** {video_title}\n**Requested by:** {message.from_user.first_name}"
        await client.send_video(
            message.chat.id,
            video=open(video_file, "rb"),
            caption=cap,
            thumb=video_thumbnail
        )

        # Clean up the temporary files
        os.remove(video_file)
        await m.delete()

    except Exception as e:
        await m.edit("**Error:** Unable to download the video. Please try again later.")
        print(str(e))
