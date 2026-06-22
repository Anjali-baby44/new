# PritiMusic/plugins/admins/autoplay.py

from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from PritiMusic import app
from PritiMusic.utils.database.autoplay import (
    is_autoplay_group,
    add_autoplay_group,
    remove_autoplay_group,
)
from PritiMusic.utils.decorators import AdminRightsCheck
from config import BANNED_USERS


PHOTO_URL = "https://files.catbox.moe/wktt8l.jpg"


def get_panel(chat_id, enabled):
    status = "🟢 𝐄ɴᴀʙʟᴇᴅ" if enabled else "🔴 𝐃ɪsᴀʙʟᴇᴅ"

    caption = f"""
**🎵 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ 𝐒ᴇᴛᴛɪɴɢ𝐬**

➻ 𝐌ᴀɴᴀɢᴇ 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ ғᴇᴀᴛᴜʀᴇ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.

**✦ 𝐂ᴜʀʀᴇɴᴛ 𝐒ᴛᴀᴛᴜ𝐬**
{status}

━━━━━━━━━━━━━━━
⚡ 𝐏ᴏᴡᴇʀᴇᴅ ʙʏ ➛ 𝐊ᴀᴠʏᴀ𝐁ᴏᴛ𝐬
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 𝐄ɴᴀʙʟᴇ",
                    callback_data=f"AUTOPLAY_ENABLE|{chat_id}",
                ),
                InlineKeyboardButton(
                    "🔴 𝐃ɪsᴀʙʟᴇ",
                    callback_data=f"AUTOPLAY_DISABLE|{chat_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"⚡ 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ : {status}",
                    callback_data="AUTOPLAY_STATUS",
                )
            ],
        ]
    )

    return caption, buttons


@app.on_message(
    filters.command(["autoplay"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def autoplay_mode(client, message: Message, _, chat_id):
    enabled = await is_autoplay_group(chat_id)

    caption, buttons = get_panel(chat_id, enabled)

    await message.reply_photo(
        photo=PHOTO_URL,
        caption=caption,
        reply_markup=buttons,
    )


@app.on_callback_query(filters.regex("^AUTOPLAY_ENABLE"))
async def autoplay_enable(_, query: CallbackQuery):
    chat_id = int(query.data.split("|")[1])

    await add_autoplay_group(chat_id)

    caption, buttons = get_panel(chat_id, True)

    await query.message.edit_caption(
        caption=caption,
        reply_markup=buttons,
    )

    await query.answer("Auto Play Enabled ✅")


@app.on_callback_query(filters.regex("^AUTOPLAY_DISABLE"))
async def autoplay_disable(_, query: CallbackQuery):
    chat_id = int(query.data.split("|")[1])

    await remove_autoplay_group(chat_id)

    caption, buttons = get_panel(chat_id, False)

    await query.message.edit_caption(
        caption=caption,
        reply_markup=buttons,
    )

    await query.answer("Auto Play Disabled ❌")


@app.on_callback_query(filters.regex("^AUTOPLAY_STATUS"))
async def autoplay_status(_, query: CallbackQuery):
    await query.answer(
        "Auto Play Status Panel",
        show_alert=False,
    )
