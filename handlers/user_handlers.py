import random
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, GREETINGS
import database as db

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    # Check if banned
    if db.is_user_banned(user.id):
        await message.reply_text("🚫 You have been banned from using this bot.")
        return
    
    # Update last active
    db.update_last_active(user.id)
    
    # Owner sending to specific user
    if user.id == OWNER_ID and context.user_data.get('send_to_user'):
        target_user_id = context.user_data['send_to_user']
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 <b>Message from Sam:</b>\n\n{message.text}",
                parse_mode='HTML'
            )
            await message.reply_text(f"✅ Message sent to user {target_user_id}!")
        except Exception as e:
            await message.reply_text(f"❌ Failed to send: {str(e)}")
        context.user_data['send_to_user'] = None
        return
    
    # Owner broadcast mode
    if user.id == OWNER_ID and context.user_data.get('broadcast_mode'):
        users = db.get_all_users()
        success = 0
        failed = 0
        
        for u in users:
            try:
                await context.bot.send_message(
                    chat_id=u['user_id'],
                    text=f"📢 <b>Broadcast from Sam:</b>\n\n{message.text}",
                    parse_mode='HTML'
                )
                success += 1
            except:
                failed += 1
        
        await message.reply_text(
            f"✅ Broadcast complete!\n\n"
            f"Sent: {success}\n"
            f"Failed: {failed}"
        )
        context.user_data['broadcast_mode'] = False
        return
    
    # Owner receiving payment QR/UPI
    if user.id == OWNER_ID and context.user_data.get('awaiting_payment_info'):
        await message.reply_text("Please send QR code image first, then UPI ID")
        return
    
    # Regular user sending to owner
    if user.id != OWNER_ID:
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"📩 <b>Message from {user.first_name}</b> (@{user.username or 'no_username'})\n"
                     f"ID: {user.id}\n\n{message.text}",
                parse_mode='HTML'
            )
            greeting = random.choice(GREETINGS)
            await message.reply_text(greeting)
        except Exception as e:
            await message.reply_text("❌ Failed to send message. Please try again later.")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    if db.is_user_banned(user.id):
        await message.reply_text("🚫 You have been banned from using this bot.")
        return
    
    db.update_last_active(user.id)
    
    # Owner handling payment QR
    if user.id == OWNER_ID and context.user_data.get('awaiting_payment_info') and message.photo:
        file_id = message.photo[-1].file_id
        context.user_data['payment_qr'] = file_id
        await message.reply_text("✅ QR Code saved! Now send me the UPI ID:")
        return
    
    # Owner sending media to specific user
    if user.id == OWNER_ID and context.user_data.get('send_to_user'):
        target_user_id = context.user_data['send_to_user']
        try:
            caption = f"💬 <b>Message from Sam:</b>\n\n{message.caption or ''}"
            
            if message.photo:
                await context.bot.send_photo(target_user_id, message.photo[-1].file_id, caption=caption, parse_mode='HTML')
            elif message.video:
                await context.bot.send_video(target_user_id, message.video.file_id, caption=caption, parse_mode='HTML')
            elif message.document:
                await context.bot.send_document(target_user_id, message.document.file_id, caption=caption, parse_mode='HTML')
            elif message.audio:
                await context.bot.send_audio(target_user_id, message.audio.file_id, caption=caption, parse_mode='HTML')
            elif message.voice:
                await context.bot.send_voice(target_user_id, message.voice.file_id, caption=caption, parse_mode='HTML')
            
            await message.reply_text(f"✅ Media sent to user {target_user_id}!")
        except Exception as e:
            await message.reply_text(f"❌ Failed to send: {str(e)}")
        context.user_data['send_to_user'] = None
        return
    
    # Owner broadcast mode
    if user.id == OWNER_ID and context.user_data.get('broadcast_mode'):
        users = db.get_all_users()
        success = 0
        failed = 0
        caption = f"📢 <b>Broadcast from Sam:</b>\n\n{message.caption or ''}"
        
        for u in users:
            try:
                if message.photo:
                    await context.bot.send_photo(u['user_id'], message.photo[-1].file_id, caption=caption, parse_mode='HTML')
                elif message.video:
                    await context.bot.send_video(u['user_id'], message.video.file_id, caption=caption, parse_mode='HTML')
                elif message.document:
                    await context.bot.send_document(u['user_id'], message.document.file_id, caption=caption, parse_mode='HTML')
                success += 1
            except:
                failed += 1
        
        await message.reply_text(f"✅ Broadcast complete!\n\nSent: {success}\nFailed: {failed}")
        context.user_data['broadcast_mode'] = False
        return
    
    # Regular user sending media to owner
    if user.id != OWNER_ID:
        try:
            caption = f"📩 <b>Media from {user.first_name}</b> (@{user.username or 'no_username'})\nID: {user.id}\n\n{message.caption or ''}"
            
            if message.photo:
                await context.bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=caption, parse_mode='HTML')
            elif message.video:
                await context.bot.send_video(OWNER_ID, message.video.file_id, caption=caption, parse_mode='HTML')
            elif message.document:
                await context.bot.send_document(OWNER_ID, message.document.file_id, caption=caption, parse_mode='HTML')
            elif message.audio:
                await context.bot.send_audio(OWNER_ID, message.audio.file_id, caption=caption, parse_mode='HTML')
            elif message.voice:
                await context.bot.send_voice(OWNER_ID, message.voice.file_id, caption=caption, parse_mode='HTML')
            
            greeting = random.choice(GREETINGS)
            await message.reply_text(greeting)
        except Exception as e:
            await message.reply_text("❌ Failed to send media. Please try again later.")

async def handle_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    if db.is_user_banned(user.id):
        await message.reply_text("🚫 You have been banned from using this bot.")
        return
    
    if user.id == OWNER_ID and context.user_data.get('broadcast_mode'):
        users = db.get_all_users()
        success = 0
        
        for u in users:
            try:
                await context.bot.forward_message(
                    chat_id=u['user_id'],
                    from_chat_id=message.chat_id,
                    message_id=message.message_id
                )
                success += 1
            except:
                pass
        
        await message.reply_text(f"✅ Poll broadcast to {success} users!")
        context.user_data['broadcast_mode'] = False
    elif user.id != OWNER_ID:
        try:
            await context.bot.forward_message(
                chat_id=OWNER_ID,
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"📊 Poll from {user.first_name} (@{user.username or 'no_username'})\nID: {user.id}"
            )
            greeting = random.choice(GREETINGS)
            await message.reply_text(greeting)
        except:
            await message.reply_text("❌ Failed to send poll.")
