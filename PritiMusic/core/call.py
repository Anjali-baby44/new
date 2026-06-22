import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded
from pyrogram.enums import ParseMode

import config
from PritiMusic import LOGGER, YouTube, app
from PritiMusic.misc import db
from PritiMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from PritiMusic.utils.exceptions import AssistantErr
from PritiMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from PritiMusic.utils.inline.play import stream_markup, telegram_markup
from PritiMusic.utils.stream.autoclear import auto_clean
from strings import get_string
from PritiMusic.utils.thumbnails import get_thumb

autoend = {}
counter = {}

FORCE_JOIN_LINKS = [
    "https://t.me/betabot_hub",
    "https://t.me/betabot_support",
    "https://t.me/sukoon_s",
]

# ✅ Helper for Random Image
def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # Fallback

async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="LuckyAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        
        self.custom_assistants = {} 
        self.active_clients = {} 

    async def get_active_clients(self, chat_id):
        clients = []
        if chat_id in self.active_clients:
            val = self.active_clients[chat_id]
            if isinstance(val, list):
                clients.extend(val)
            else:
                clients.append(val)
        
        if not clients:
            try:
                main_ass = await group_assistant(self, chat_id)
                clients.append(main_ass)
            except:
                clients.append(self.one)
        
        return list(set(clients))

    async def pause_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.pause_stream(chat_id)
            except:
                pass

    async def resume_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.resume_stream(chat_id)
            except:
                pass

    async def stop_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        try:
            await _clear_(chat_id)
        except:
            pass
            
        for assistant in assistants:
            try:
                await assistant.leave_group_call(chat_id)
            except:
                pass
        
        if chat_id in self.active_clients:
            del self.active_clients[chat_id]

    async def stop_stream_force(self, chat_id: int):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.leave_group_call(chat_id)
            except:
                pass
        
        if chat_id in self.active_clients:
            del self.active_clients[chat_id]
            
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistants = await self.get_active_clients(chat_id)
        assistant = assistants[0] if assistants else self.one
        
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
            
        dur = await loop.run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            for assistant in assistants:
                try:
                    await assistant.change_stream(chat_id, stream)
                except:
                    pass
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
        assistant_type=None 
    ):
        assistants = await self.get_active_clients(chat_id)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
            
        for assistant in assistants:
            try:
                await assistant.change_stream(
                    chat_id,
                    stream,
                )
            except Exception as e:
                pass

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistants = await self.get_active_clients(chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        for assistant in assistants:
            try:
                await assistant.change_stream(chat_id, stream)
            except:
                pass

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(
            config.LOGGER_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
        userbot=None,
    ):
        assistant_to_join = None
        
        if userbot:
            if FORCE_JOIN_LINKS:
                for link_join in FORCE_JOIN_LINKS:
                    try:
                        await userbot.join_chat(link_join)
                        await asyncio.sleep(1) 
                    except:
                        pass
            
            user_id = userbot.me.id
            if user_id in self.custom_assistants:
                assistant_to_join = self.custom_assistants[user_id]
            else:
                assistant_to_join = PyTgCalls(
                    userbot,
                    cache_duration=100
                )
                await assistant_to_join.start()
                
                @assistant_to_join.on_stream_end()
                async def stream_end_handler(client, update: Update):
                    if not isinstance(update, StreamAudioEnded):
                        return
                    await self.change_stream(client, update.chat_id)

                @assistant_to_join.on_kicked()
                @assistant_to_join.on_closed_voice_chat()
                @assistant_to_join.on_left()
                async def stream_services_handler(_, chat_id: int):
                    await self.stop_stream(chat_id)
                
                self.custom_assistants[user_id] = assistant_to_join

        else:
            assistant_to_join = await group_assistant(self, chat_id)
        
        if chat_id not in self.active_clients:
            self.active_clients[chat_id] = []
        
        if assistant_to_join not in self.active_clients[chat_id]:
            self.active_clients[chat_id].append(assistant_to_join)
        
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = (
                AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
                if video
                else AudioPiped(link, audio_parameters=HighQualityAudio())
            )
        try:
            await assistant_to_join.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant_to_join.get_participants(chat_id))
                if users == 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except:
                pass

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)

            # ==========================================
            # 🔄 AUTOPLAY BLOCK 
            # ==========================================
            if not check:
                from PritiMusic.utils.database.autoplay import is_autoplay_group
                try:
                    auto_on = await is_autoplay_group(chat_id)
                except:
                    auto_on = False

                if auto_on and popped:
                    LOGGER(__name__).info(f"🔄 Autoplay active searching next song for {chat_id}")
                    raw_title = popped.get("title", "Unknown Title")
                    title_lower = str(raw_title).lower()
                    last_vidid = str(popped.get("vidid", ""))

                    keywords_map = {
                        "Punjabi": ["sidhu moose wala", "karan aujla", "diljit dosanjh", "ap dhillon", "shubh", "kaka", "hardy sandhu", "guru randhawa", "b praak", "jass manak"],
                        "Bhojpuri": ["pawan singh", "khesari lal yadav", "shilpi raj", "antra singh", "pramod premi", "ritesh pandey", "arvind akela kallu", "gunjan singh"],
                        "Haryanvi": ["sapna choudhary", "renuka panwar", "gulzaar chhaniwala", "sumit goswami", "raju punjabi", "amit saini rohtakiya", "pranjal dahiya"],
                        "Hindi": ["arijit singh", "neha kakkar", "shreya ghoshal", "jubin nautiyal", "atif aslam", "darshan raval", "armaan malik", "sonu nigam", "yo yo honey singh", "badshah", "sunidhi chauhan", "udit narayan", "kumar sanu", "alka yagnik", "sachet tandon", "parampara", "bollywood"],
                        "Tamil": ["anirudh", "ar rahman", "rahman", "yuvan shankar raja", "sid sriram", "harris jayaraj", "vijay prakash", "s.p. balasubrahmanyam", "kollywood"],
                        "Telugu": ["devi sri prasad", "dsp", "thaman", "sid sriram", "anurag kulkarni", "mangli", "geetha madhuri", "allu", "ramarao", "tollywood"],
                        "English": ["taylor swift", "justin bieber", "ed sheeran", "ariana grande", "the weeknd", "drake", "eminem", "billie eilish", "dua lipa", "bruno mars", "post malone", "pop song"],
                        "Urdu": ["rahat fateh ali khan", "nusrat fateh ali khan", "ali zafar", "qurat-ul-ain balouch", "coke studio pakistan", "urdu", "ghazal"],
                        "Kannada": ["puneeth rajkumar", "sanjith hegde", "chandan shetty", "vijay prakash", "kannada", "sandalwood"],
                        "Myanmar": ["sai sai kham leng", "ni ni khin zaw", "lay phyu", "myanmar song", "burmese"]
                    }

                    detected_lang = "Hindi"
                    detected_artist = None

                    for lang, kws in keywords_map.items():
                        match = next((kw for kw in kws if kw in title_lower), None)
                        if match:
                            detected_lang = lang
                            if match not in ["bollywood", "kollywood", "tollywood", "pop song", "urdu", "ghazal", "kannada", "sandalwood", "myanmar song", "burmese"]:
                                detected_artist = match
                            break

                    if detected_artist:
                        search_query = random.choice([
                            f"{detected_artist} latest hit single official video",
                            f"{detected_artist} trending track lyrical",
                            f"{detected_artist} superhit popular track audio",
                            f"{detected_artist} best song official"
                        ])
                    else:
                        lang_pools = {
                            "Hindi": ["hindi single track official video", "bollywood latest lyrical hit song", "trending hindi pop music"],
                            "Punjabi": ["latest punjabi single official video", "punjabi trending track lyrical", "punjabi pop hit track"],
                            "Bhojpuri": ["bhojpuri latest single video song", "bhojpuri trending song official", "bhojpuri hit dj remix"],
                            "Haryanvi": ["haryanvi single track official", "latest haryanvi video song", "haryanvi dj hit pop"],
                            "Tamil": ["tamil latest single official video", "kollywood trending song lyrical", "tamil hit movie track"],
                            "Telugu": ["telugu tollywood latest single song", "telugu lyrical video official", "telugu trending track"],
                            "English": ["english pop single official music video", "trending english lyrical song", "global hit english track"],
                            "Urdu": ["urdu latest hit song", "trending urdu song lyrical", "coke studio pakistan hit"],
                            "Kannada": ["kannada latest single official video", "sandalwood trending song lyrical", "kannada hit movie track"],
                            "Myanmar": ["myanmar latest single official video", "trending burmese song", "myanmar pop hit track"]
                        }
                        search_query = random.choice(lang_pools.get(detected_lang, lang_pools["Hindi"]))

                    # ✅ YOUTUBE.DETAILS FIX APPLIED HERE
                    try:
                        (
                            auto_title,
                            auto_duration_min,
                            auto_duration_sec,
                            auto_thumbnail,
                            auto_vidid,
                        ) = await YouTube.details(search_query, True)

                        if auto_title:
                            db[chat_id].append({
                                "title": str(auto_title),
                                "dur": str(auto_duration_min),
                                "streamtype": popped.get("streamtype", "audio") if popped else "audio",
                                "by": "Autoplay 🟢",
                                "user_id": 0,
                                "chat_id": chat_id,
                                "file": f"vid_{auto_vidid}",
                                "vidid": str(auto_vidid),
                                "seconds": auto_duration_sec,
                                "old_dur": str(auto_duration_min),
                                "old_second": 0,
                                "played": 0,
                                "client": popped.get("client", app) if popped else app
                            })
                            
                            # 📝 AUTOPLAY LOGGER 
                            try:
                                await app.send_message(
                                    config.LOGGER_ID,
                                    f"**🔄 Autoplay Triggered**\n\n**Chat ID:** `{chat_id}`\n**Queued Track:** {auto_title}\n**Language/Genre:** {detected_lang}"
                                )
                            except Exception:
                                pass

                    except Exception as e:
                        LOGGER(__name__).error(f"❌ Autoplay exception: {e}")

            if not db.get(chat_id): # If queue is still empty after Autoplay attempt
                await _clear_(chat_id)
                if chat_id in self.active_clients:
                    del self.active_clients[chat_id]
                return await client.leave_group_call(chat_id)

        except Exception as e:
            try:
                await _clear_(chat_id)
                if chat_id in self.active_clients:
                    del self.active_clients[chat_id]
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = db[chat_id][0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (db[chat_id][0]["title"]).title()
            user = db[chat_id][0]["by"]
            user_id = db[chat_id][0].get("user_id", 0) 
            original_chat_id = db[chat_id][0]["chat_id"]
            streamtype = db[chat_id][0]["streamtype"]
            videoid = db[chat_id][0]["vidid"]
            
            chat_client = db[chat_id][0].get("client")
            if not chat_client:
                chat_client = app

            db[chat_id][0]["played"] = 0
            exis = (db[chat_id][0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = db[chat_id][0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    try: await chat_client.send_message(original_chat_id, text="⚠️ **Live stream offline. Auto-skipping...**")
                    except: pass
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER

                if video:
                    stream = AudioVideoPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    try: await chat_client.send_message(original_chat_id, text="❌ **Live stream play failed. Auto-skipping...**")
                    except: pass
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER

                button = telegram_markup(_, chat_id)
                img = get_random_img(config.STREAM_IMG_URL)
                
                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            db[chat_id][0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=False 
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                except:
                    pass
                
            elif "vid_" in queued:
                mystic = await chat_client.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    try:
                        file_path, direct = await YouTube.download(
                            videoid,
                            mystic,
                            videoid=True,
                            video=True if str(streamtype) == "video" else False,
                        )
                    except:
                        try: await mystic.edit_text("⚠️ **Download Failed. Auto-skipping...**", disable_web_page_preview=True)
                        except: pass
                        await asyncio.sleep(1.5)
                        return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER
                
                if not file_path or str(file_path) == "None":
                    try: await mystic.edit_text("❌ **Track unavailable or Blocked. Auto-skipping...**")
                    except: pass
                    await asyncio.sleep(1.5)
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER

                if video:
                    stream = AudioVideoPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    try: await chat_client.send_message(original_chat_id, text="❌ **Play routing failed. Auto-skipping...**")
                    except: pass
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER
                
                img = await get_thumb(videoid, user_id, chat_client)
                if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

                button = stream_markup(_, chat_id)
                try:
                    await mystic.delete()
                except:
                    pass
                
                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            db[chat_id][0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=False 
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
                except:
                    pass
                
            elif "index_" in queued:
                stream = (
                    AudioVideoPiped(
                        videoid,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                    if str(streamtype) == "video"
                    else AudioPiped(videoid, audio_parameters=HighQualityAudio())
                )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    try: await chat_client.send_message(original_chat_id, text="❌ **Index stream failed. Auto-skipping...**")
                    except: pass
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER
                    
                button = telegram_markup(_, chat_id)
                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=get_random_img(config.STREAM_IMG_URL),
                        caption=_["stream_2"].format(user),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=False 
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                except:
                    pass
                
            else:
                if video:
                    stream = AudioVideoPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    try: await chat_client.send_message(original_chat_id, text="❌ **Play failed. Auto-skipping...**")
                    except: pass
                    return await self.change_stream(client, chat_id) # ⏭️ AUTO-SKIP TRIGGER
                    
                if videoid == "telegram":
                    button = telegram_markup(_, chat_id)
                    tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)

                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id,
                            photo=tg_img,
                            caption=_["stream_1"].format(
                                config.SUPPORT_CHAT, title[:23], db[chat_id][0]["dur"], user
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                            has_spoiler=False 
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    except: pass
                    
                elif videoid == "soundcloud":
                    button = telegram_markup(_, chat_id)
                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id,
                            photo=get_random_img(config.SOUNCLOUD_IMG_URL),
                            caption=_["stream_1"].format(
                                config.SUPPORT_CHAT, title[:23], db[chat_id][0]["dur"], user
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                            has_spoiler=False 
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    except: pass
                    
                else:
                    img = await get_thumb(videoid, user_id, chat_client)
                    if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

                    button = stream_markup(_, chat_id)
                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{app.username}?start=info_{videoid}",
                                title[:23],
                                db[chat_id][0]["dur"],
                                user,
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                            has_spoiler=False 
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "stream"
                    except: pass

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()

    async def decorators(self):
        @self.one.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.one.on_left()
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)


Lucky = Call()
