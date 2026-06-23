import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from PritiMusic import YouTube, app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.database import get_loop
from PritiMusic.utils.decorators import AdminRightsCheck
from PritiMusic.utils.inline import close_markup, stream_markup, stream_markup2
from PritiMusic.utils.stream.autoclear import auto_clean
from PritiMusic.utils.thumbnails import get_thumb
from config import BANNED_USERS

# ✅ Helper for Random Image
def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # Fallback

@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    if not len(message.command) < 2:
        loop = await get_loop(chat_id)
        if loop != 0:
            return await message.reply_text(_["admin_8"])
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            check = db.get(chat_id)
            if check:
                count = len(check)
                if count > 2:
                    count = int(count - 1)
                    if 1 <= state <= count:
                        for x in range(state):
                            popped = None
                            try:
                                popped = check.pop(0)
                            except:
                                return await message.reply_text(_["admin_12"])
                            if popped:
                                await auto_clean(popped)
                        if not check:
                            # 🔄 AUTOPLAY FAILSAFE FOR MULTI-SKIP
                            if popped:
                                db[chat_id].append(popped) # Backup for call.py to read
                            try:
                                await message.reply_text(
                                    text="🔄 **Skipped to end of queue. Triggering Autoplay...**",
                                    reply_markup=close_markup(_),
                                )
                                return await Lucky.change_stream(cli, chat_id)
                            except:
                                return
                    else:
                        return await message.reply_text(_["admin_11"].format(count))
                else:
                    return await message.reply_text(_["admin_10"])
            else:
                return await message.reply_text(_["queue_2"])
        else:
            return await message.reply_text(_["admin_9"])
    else:
        check = db.get(chat_id)
        
        # 🟢 FIX: Agar queue me sirf 1 gaana bacha hai to pop mat karo. 
        # Sidha change_stream ko pass karo taki wo data padh ke autoplay chalu kar sake!
        if len(check) == 1:
            try:
                await message.reply_text(
                    text="🔄 **Queue is empty! Triggering Autoplay...**",
                    reply_markup=close_markup(_),
                )
                return await Lucky.change_stream(cli, chat_id)
            except:
                return

        # Agar queue me aur bhi gaane hain, toh normally skip karo
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)
        except:
            pass
            
    # ⏭️ IF QUEUE IS NOT EMPTY, CONTINUE WITH NEXT SONG
    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None
    db[chat_id][0]["played"] = 0
    exis = (check[0]).get("old_dur")
    if exis:
        db[chat_id][0]["dur"] = exis
        db[chat_id][0]["seconds"] = check[0]["old_second"]
        db[chat_id][0]["speed_path"] = None
        db[chat_id][0]["speed"] = 1.0
        
    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_7"].format(title))
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Lucky.skip_stream(chat_id, link, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
        button = stream_markup2(_, chat_id)
        
        # ✅ Safe Random Image Fetch
        img = await get_thumb(videoid, message.from_user.id, message.from_user.first_name)
        if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
            has_spoiler=False 
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
        
    elif "vid_" in queued:
        mystic = await message.reply_text(_["call_7"], disable_web_page_preview=True)
        try:
            file_path, direct = await YouTube.download(
                videoid,
                mystic,
                videoid=True,
                video=status,
            )
        except:
            return await mystic.edit_text(_["call_6"])
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Lucky.skip_stream(chat_id, file_path, video=status, image=image)
        except:
            return await mystic.edit_text(_["call_6"])
        button = stream_markup(_, chat_id)
        
        # ✅ Safe Random Image Fetch
        img = await get_thumb(videoid, message.from_user.id, message.from_user.first_name)
        if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
            has_spoiler=False 
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()
        
    elif "index_" in queued:
        try:
            await Lucky.skip_stream(chat_id, videoid, video=status)
        except:
            return await message.reply_text(_["call_6"])
        button = stream_markup2(_, chat_id)
        
        # ✅ Random Stream Image
        run = await message.reply_photo(
            photo=get_random_img(config.STREAM_IMG_URL),
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
            has_spoiler=False 
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
        
    else:
        if videoid == "telegram":
            image = None
        elif videoid == "soundcloud":
            image = None
        else:
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
        try:
            await Lucky.skip_stream(chat_id, queued, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
            
        if videoid == "telegram":
            button = stream_markup2(_, chat_id)
            tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)

            run = await message.reply_photo(
                photo=tg_img,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=False 
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            
        elif videoid == "soundcloud":
            button = stream_markup2(_, chat_id)
            sc_img = get_random_img(config.SOUNCLOUD_IMG_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)

            run = await message.reply_photo(
                photo=sc_img,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=False 
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            
        else:
            button = stream_markup(_, chat_id)
            img = await get_thumb(videoid, message.from_user.id, message.from_user.first_name)
            if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

            run = await message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=False 
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
