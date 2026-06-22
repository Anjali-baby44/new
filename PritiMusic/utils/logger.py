import random
from button import ButtonStyle
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from PritiMusic import app
from PritiMusic.utils.database import is_on_off
from config import LOGGER_ID

# ✅ NEW: Add/Remove Picture URL
ADD_REMOVE_PIC = "https://files.catbox.moe/10zwqs.jpg"

# ====================================================
# HELPER FUNCTION: To Fetch Group Owner
# ====================================================
async def get_owner(client, chat_id):
    try:
        async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER:
                return member.user.mention
    except:
        pass
    return "Unknown"


async def play_logs(message, streamtype):
    if await is_on_off(2):
        try:
            query = message.text.split(None, 1)[1]
        except:
            query = "Link/File or Reply"

        # Fetch Total Members & Owner
        try:
            members_count = await app.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(app, message.chat.id)

        # Generate Link for Button
        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await app.export_chat_invite_link(message.chat.id)
            except:
                pass

        logger_text = f"""
<blockquote><b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ : {message.from_user.mention}</b>
<b>• ǫᴜᴇʀʏ : {query}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        # Create Button Markup
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.PRIMARY, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            except:
                pass
        return


async def clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype):
    # 1. Data Extract kar lete hain
    bot = await client.get_me()
    try:
        query = message.text.split(None, 1)[1]
    except:
        query = "Link/File or Reply"

    # ====================================================
    # CASE 1: Clone Bot Owner ke Logger me bhejna
    # ====================================================
    if clone_logger_id:
        owner_log_text = f"""
<b><a href="https://t.me/{bot.username}">{bot.first_name}</a> ᴘʟᴀʏ ʟᴏɢ</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ :</b> {message.from_user.mention}
<b>• ǫᴜᴇʀʏ :</b> {query}
<b>• ᴄʜᴀᴛ :</b> {message.chat.title} [<code>{message.chat.id}</code>]
"""     
        owner_reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")]]
        )

        if message.chat.id != int(clone_logger_id):
            try:
                await client.send_message(
                    chat_id=int(clone_logger_id),
                    text=owner_log_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=owner_reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending to Clone Owner Log Failed: {e}")

    # ====================================================
    # CASE 2: Aapke (Main Admin) Logger me bhejna
    # ====================================================
    if LOGGER_ID:
        try:
            members_count = await client.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(client, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await client.export_chat_invite_link(message.chat.id)
            except:
                pass

        admin_log_text = f"""
<blockquote><b>🤖 ᴄʟᴏɴᴇ ʙᴏᴛ ʟᴏɢ : @{bot.username}</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ : {message.from_user.mention}</b>
<b>• ǫᴜᴇʀʏ : {query}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.PRIMARY, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=admin_log_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[ERROR] Sending to Main Admin Log Failed: {e}")

# ====================================================
# NEW FUNCTION: Bot Added Logs (With Picture)
# ====================================================
async def bot_added_logs(client, message, is_clone=False):
    try:
        bot = await client.get_me()
        
        if message.from_user:
            added_by = message.from_user.mention
        else:
            added_by = "<b>Unknown User</b>"
        
        try:
            members_count = await client.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(client, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await client.export_chat_invite_link(message.chat.id)
            except:
                pass

        if is_clone:
            header_text = "🎉 ᴄʟᴏɴᴇ ʙᴏᴛ ᴀᴅᴅᴇᴅ"
            bot_details = f"@{bot.username}"
        else:
            header_text = "🎉 ᴍᴀɪɴ ʙᴏᴛ ᴀᴅᴅᴇᴅ"
            bot_details = app.mention

        add_log_text = f"""
<blockquote><b>{header_text}</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ᴀᴅᴅᴇᴅ ʙʏ : {added_by}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.SUCCESS, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        if LOGGER_ID:
            try:
                # 🟢 Changed from send_message to send_photo
                await app.send_photo(
                    chat_id=LOGGER_ID,
                    photo=ADD_REMOVE_PIC,
                    caption=add_log_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending Add Log Failed: {e}")
    except Exception as e:
        print(f"[ERROR] Bot Added Log Generation Failed: {e}")

# ====================================================
# UPDATED FUNCTION: Bot Removed Logs (With Picture)
# ====================================================
async def bot_removed_logs(client, message, is_clone=False):
    try:
        bot = await client.get_me()
        
        if message.from_user:
            kicked_by = message.from_user.mention
        else:
            kicked_by = "<b>Unknown User</b>"
        
        try:
            members_count = await client.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(client, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"

        if is_clone:
            header_text = "⚠️ ᴄʟᴏɴᴇ ʙᴏᴛ ʀᴇᴍᴏᴠᴇᴅ"
            bot_details = f"@{bot.username}"
        else:
            header_text = "⚠️ ᴍᴀɪɴ ʙᴏᴛ ʀᴇᴍᴏᴠᴇᴅ"
            bot_details = app.mention

        remove_log_text = f"""
<blockquote><b>{header_text}</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {kicked_by}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.DANGER, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        if LOGGER_ID:
            try:
                # 🟢 Changed from send_message to send_photo
                await app.send_photo(
                    chat_id=LOGGER_ID,
                    photo=ADD_REMOVE_PIC,
                    caption=remove_log_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending Remove Log Failed: {e}")
    except Exception as e:
        print(f"[ERROR] Bot Removed Log Generation Failed: {e}")


# ====================================================
# Autoplay Logs
# ====================================================
async def autoplay_log(client, chat_id, query, is_clone=False, clone_logger_id=None):
    if not await is_on_off(2):
        return
        
    try:
        bot = await client.get_me()
        bot_mention = bot.mention
    except:
        return

    try:
        chat = await client.get_chat(chat_id)
        chat_title = chat.title
        chat_username = chat.username
    except:
        chat_title = "Unknown Chat"
        chat_username = None

    try:
        members_count = await client.get_chat_members_count(chat_id)
    except:
        members_count = "Unknown"
        
    owner = await get_owner(client, chat_id)

    chat_link = None
    if chat_username:
        chat_link = f"https://t.me/{chat_username}"
    else:
        try:
            chat_link = await client.export_chat_invite_link(chat_id)
        except:
            pass

    # ====================================================
    # CASE 1: Clone Bot Owner ke Logger me bhejna
    # ====================================================
    if is_clone and clone_logger_id:
        owner_autoplay_text = f"""
<b><a href="https://t.me/{bot.username}">{bot.first_name}</a> ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>

<b>• ᴀᴄᴛɪᴏɴ : ᴀᴜᴛᴏᴘʟᴀʏ ᴛʀɪɢɢᴇʀᴇᴅ 🔄</b>
<b>• ᴛʀᴀᴄᴋ :</b> {query}
<b>• ᴄʜᴀᴛ :</b> {chat_title} [<code>{chat_id}</code>]
"""
        owner_reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")]]
        )

        if chat_id != int(clone_logger_id):
            try:
                await client.send_message(
                    chat_id=int(clone_logger_id),
                    text=owner_autoplay_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=owner_reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending to Clone Owner Autoplay Log Failed: {e}")

    # ====================================================
    # CASE 2: Aapke (Main Admin) Logger me bhejna
    # ====================================================
    if is_clone:
        header_text = f"🤖 <b>ᴄʟᴏɴᴇ ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ : @{bot.username}</b>"
    else:
        header_text = f"<b>{bot_mention} ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>"

    logger_text = f"""
<blockquote>{header_text}

<b>• ᴀᴄᴛɪᴏɴ : ᴀᴜᴛᴏᴘʟᴀʏ ᴛʀɪɢɢᴇʀᴇᴅ 🔄</b>
<b>• ᴛʀᴀᴄᴋ : {query}</b>
<b>• ᴄʜᴀᴛ : {chat_title} [<code>{chat_id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
    buttons = []
    if chat_link:
        buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.SUCCESS, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
    buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
    
    reply_markup = InlineKeyboardMarkup(buttons)

    if chat_id != LOGGER_ID:
        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=logger_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[ERROR] Sending Autoplay Log Failed: {e}")
