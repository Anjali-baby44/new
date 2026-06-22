import asyncio
from pyrogram import filters, Client
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, RPCError, PeerIdInvalid, UserIsBlocked, UserDeactivated, AuthKeyUnregistered

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database.clonedb import (
    get_all_clones, 
    get_served_chats_clone, 
    get_served_users_clone,
    get_clonebot_owner
)
from config import API_ID, API_HASH

# Global Flag
IS_CBROADCASTING = False

# ==========================================
# 🗑️ CLONE AUTO-DELETE HELPER (24 HOURS)
# ==========================================
async def auto_delete_clone_message(chat_id: int, message_id: int, bot_token: str):
    """Waits 24 hours, connects temporarily via clone token, and deletes the message."""
    await asyncio.sleep(24 * 3600)  # 24 hours in seconds (86,400 seconds)
    try:
        async with Client(
            "memory",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            in_memory=True,
            no_updates=True
        ) as temp_client:
            await temp_client.delete_messages(chat_id, message_id)
    except Exception:
        pass


@app.on_message(filters.command("stopcbroadcast") & SUDOERS)
async def stop_clone_broadcast(client, message):
    global IS_CBROADCASTING
    if not IS_CBROADCASTING:
        return await message.reply_text("❌ **No Clone Broadcast is currently running.**")
    
    IS_CBROADCASTING = False
    await message.reply_text("🛑 **Stopping Broadcast...**\nProcess will halt after current bot.")


@app.on_message(filters.command("cbroadcast") & SUDOERS)
async def clone_broadcast_handler(client, message):
    global IS_CBROADCASTING
    
    if IS_CBROADCASTING:
        return await message.reply_text("⚠️ **Broadcast already running!** Stop it first baby.")

    # --- COMMAND PARSING ---
    content = message.text or message.caption

    if message.reply_to_message:
        query = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if not content or len(message.command) < 2:
            return await message.reply_text(
                "<b>📣 Clone Broadcast Manager</b>\n\n"
                "<b>Usage:</b> `/cbroadcast [Message] [Flags]`\n"
                "<b>Flags:</b> `-owner`, `-user`, `-group`, `-all`, `-pin`"
            )
        query = content.split(None, 1)[1]

    pin = "-pin" in content if content else False
    send_owners = "-owner" in content or "-all" in content if content else False
    send_users = "-user" in content or "-all" in content if content else False
    send_groups = "-group" in content or "-all" in content if content else False

    if not send_users and not send_groups and not send_owners:
        send_groups = True

    if query:
        for flag in ["-pin", "-owner", "-user", "-group", "-all"]:
            query = query.replace(flag, "")
        query = query.strip()

    if not query and not message.reply_to_message:
        return await message.reply_text("❌ **Message is empty!**")

    IS_CBROADCASTING = True
    status_msg = await message.reply_text("🔄 **Analyzing Clones Baby...**")

    # --- FETCH CLONES ---
    all_clones_data = []
    try:
        async for c in get_all_clones():
            all_clones_data.append(c)
    except Exception as e:
        IS_CBROADCASTING = False
        return await status_msg.edit_text(f"❌ **DB Error:** {e}")

    total_clones = len(all_clones_data)
    if total_clones == 0:
        IS_CBROADCASTING = False
        return await status_msg.edit_text("❌ **No Clones Found.**")

    await status_msg.edit_text(f"🚀 **Targeting {total_clones} Clones...**")

    success_clones = 0
    failed_clones = 0
    total_sent = 0
    
    total_targetted_groups = 0
    total_targetted_users = 0

    # --- MAIN LOOP ---
    for clone in all_clones_data:
        if not IS_CBROADCASTING: break

        token = clone.get('token')
        bot_id = clone.get('bot_id')
        username = clone.get('username', 'Unknown')

        if not token or not bot_id:
            failed_clones += 1
            continue

        # --- A. COLLECT TARGETS ---
        target_ids = set()

        if send_owners:
            try:
                owner = await get_clonebot_owner(bot_id)
                if owner:
                    target_ids.add(int(owner))
                    total_targetted_users += 1
            except: pass

        if send_users:
            try:
                users_list = await get_served_users_clone(bot_id)
                total_targetted_users += len(users_list)
                for u in users_list:
                    target_ids.add(int(u['user_id']))
            except: pass

        if send_groups:
            try:
                chats_list = await get_served_chats_clone(bot_id)
                total_targetted_groups += len(chats_list)
                for c in chats_list:
                    target_ids.add(int(c['chat_id']))
            except: pass

        if not target_ids:
            continue

        # --- B. SEND MESSAGES ---
        try:
            async with Client(
                f":memory:",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                in_memory=True,
                no_updates=True
            ) as clone_app:
                
                clone_sent_count = 0
                
                try:
                    await clone_app.get_me()
                except (AuthKeyUnregistered, UserDeactivated):
                    failed_clones += 1
                    continue

                for chat_id in target_ids:
                    if not IS_CBROADCASTING: break
                    
                    try:
                        sent = None
                        # 🔥 FIX: Forcing Clone App to send the replied media/text natively
                        if message.reply_to_message:
                            rep = message.reply_to_message
                            if rep.photo:
                                sent = await clone_app.send_photo(chat_id, photo=rep.photo.file_id, caption=query)
                            elif rep.video:
                                sent = await clone_app.send_video(chat_id, video=rep.video.file_id, caption=query)
                            elif rep.audio:
                                sent = await clone_app.send_audio(chat_id, audio=rep.audio.file_id, caption=query)
                            elif rep.document:
                                sent = await clone_app.send_document(chat_id, document=rep.document.file_id, caption=query)
                            elif rep.animation:
                                sent = await clone_app.send_animation(chat_id, animation=rep.animation.file_id, caption=query)
                            elif rep.sticker:
                                sent = await clone_app.send_sticker(chat_id, sticker=rep.sticker.file_id)
                            else:
                                sent = await clone_app.send_message(chat_id, text=query)
                        else:
                            sent = await clone_app.send_message(chat_id, text=query)
                        
                        # 🗑️ Trigger 24-hour auto-delete for Clones
                        if sent:
                            try:
                                msg_id = sent[0].id if isinstance(sent, list) else sent.id
                                asyncio.create_task(auto_delete_clone_message(chat_id, msg_id, token))
                            except: pass

                        if pin and sent and str(chat_id).startswith("-100"):
                            try:
                                msg_to_pin = sent[0] if isinstance(sent, list) else sent
                                await msg_to_pin.pin(disable_notification=True)
                            except: pass
                        
                        clone_sent_count += 1
                        total_sent += 1
                        await asyncio.sleep(0.2)
                    
                    except FloodWait as e:
                        await asyncio.sleep(int(e.value))
                    except (RPCError, PeerIdInvalid, UserIsBlocked):
                        continue
                    except Exception:
                        continue
                
                if clone_sent_count > 0:
                    success_clones += 1
                
        except Exception:
            failed_clones += 1
            continue

    # --- FINAL REPORT ---
    IS_CBROADCASTING = False
    
    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"🤖 **Total Clones:** {total_clones}\n"
        f"📢 **Active Sending:** {success_clones}\n"
        f"⚠️ **Failed/Revoked:** {failed_clones}\n"
        f"📨 **Messages Sent:** {total_sent}\n\n"
        f"👥 **Total Users:** {total_targetted_users}\n"
        f"👥 **Total Groups:** {total_targetted_groups}"
    )
