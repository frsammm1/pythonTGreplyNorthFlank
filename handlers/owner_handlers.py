from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID
import database as db

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == OWNER_ID:
        await update.message.reply_text(
            f"👑 Welcome back, Sam!\n\n"
            f"Use /panel to access your owner dashboard.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📊 Owner Panel", callback_data="owner_panel")
            ]])
        )
    else:
        db.add_user(user.id, user.username, user.first_name)
        keyboard = [
            [InlineKeyboardButton("📩 Send Message to Sam", callback_data="send_to_owner")],
            [InlineKeyboardButton("🤖 Get Bot Clone", callback_data="get_clone")]
        ]
        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            f"Welcome to Sam's Bot! 🌟\n\n"
            f"You can:\n"
            f"• Send messages directly to Sam\n"
            f"• Get your own bot clone\n\n"
            f"Choose an option below:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        if query:
            await query.answer("❌ Access denied!")
        return
    
    user_count = db.get_user_count()
    banned_count = len(db.get_banned_users())
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="show_stats")],
        [InlineKeyboardButton("👥 Active Users", callback_data="list_users"),
         InlineKeyboardButton("🚫 Banned Users", callback_data="list_banned")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="start_broadcast"),
         InlineKeyboardButton("💬 Send to User", callback_data="send_to_user")],
        [InlineKeyboardButton("💳 Manage Plans", callback_data="manage_plans"),
         InlineKeyboardButton("💰 Set Payment", callback_data="set_payment")],
        [InlineKeyboardButton("🔑 Auth Keys", callback_data="manage_auth_keys"),
         InlineKeyboardButton("✅ Verify Payments", callback_data="verify_payments")]
    ]
    
    text = (
        f"👑 <b>Owner Dashboard</b>\n\n"
        f"📊 <b>Quick Stats:</b>\n"
        f"• Active Users: {user_count}\n"
        f"• Banned Users: {banned_count}\n\n"
        f"Select an option below:"
    )
    
    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    users = db.get_all_users()
    banned = db.get_banned_users()
    plans = db.get_all_plans()
    active_keys = db.get_active_auth_keys()
    
    text = (
        f"📊 <b>Detailed Statistics</b>\n\n"
        f"👥 <b>Users:</b>\n"
        f"• Total Active: {len(users)}\n"
        f"• Total Banned: {len(banned)}\n\n"
        f"💳 <b>Subscriptions:</b>\n"
        f"• Active Plans: {len(plans)}\n"
        f"• Active Keys: {len(active_keys)}\n\n"
        f"🤖 <b>Clone Bots:</b>\n"
        f"• Active Clones: {len([k for k in active_keys if k['bot_token']])}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]]
    
    await query.answer()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    users = db.get_all_users()
    
    if not users:
        await query.answer("No active users!")
        return
    
    keyboard = []
    for user in users[:20]:  # Limit to 20 for button limit
        username = user['username'] or user['first_name']
        keyboard.append([InlineKeyboardButton(
            f"👤 {username} (ID: {user['user_id']})",
            callback_data=f"user_action_{user['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    
    await query.answer()
    await query.edit_message_text(
        f"👥 <b>Active Users ({len(users)})</b>\n\n"
        f"Click on a user for actions:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    users = db.get_banned_users()
    
    if not users:
        await query.answer("No banned users!")
        await query.edit_message_text(
            "🚫 No banned users",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]])
        )
        return
    
    keyboard = []
    for user in users[:20]:
        username = user['username'] or user['first_name']
        keyboard.append([InlineKeyboardButton(
            f"🚫 {username} (ID: {user['user_id']})",
            callback_data=f"unban_{user['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    
    await query.answer()
    await query.edit_message_text(
        f"🚫 <b>Banned Users ({len(users)})</b>\n\n"
        f"Click to unban:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def manage_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    plans = db.get_all_plans()
    
    text = "💳 <b>Subscription Plans</b>\n\n"
    keyboard = []
    
    if plans:
        for plan in plans:
            text += f"• {plan['name']}: ₹{plan['price']} ({plan['days']} days)\n"
            keyboard.append([InlineKeyboardButton(
                f"❌ Delete {plan['name']}",
                callback_data=f"delete_plan_{plan['id']}"
            )])
    else:
        text += "No plans created yet."
    
    keyboard.append([InlineKeyboardButton("➕ Add Plan", callback_data="add_plan")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    
    await query.answer()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def set_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        if query:
            await query.answer("❌ Access denied!")
        return
    
    payment_info = db.get_payment_info()
    
    text = "💰 <b>Payment Information</b>\n\n"
    if payment_info:
        text += f"✅ QR Code: Set\n"
        text += f"✅ UPI ID: {payment_info['upi_id']}\n\n"
    else:
        text += "❌ Not configured yet\n\n"
    
    text += "Send me:\n1. QR Code image\n2. Then reply with UPI ID"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]]
    
    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['awaiting_payment_info'] = True

async def manage_auth_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    keys = db.get_active_auth_keys()
    
    text = "🔑 <b>Active Auth Keys</b>\n\n"
    keyboard = []
    
    if keys:
        for key in keys[:15]:
            username = key['username'] or key['first_name']
            text += f"• {username}: {key['plan_name']}\n"
            keyboard.append([InlineKeyboardButton(
                f"🔴 Revoke {username}",
                callback_data=f"revoke_key_{key['key']}"
            )])
    else:
        text += "No active keys"
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    
    await query.answer()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def verify_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id != OWNER_ID:
        await query.answer("❌ Access denied!")
        return
    
    payments = db.get_pending_payments()
    
    if not payments:
        await query.answer("No pending payments!")
        await query.edit_message_text(
            "✅ No pending payment verifications",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]])
        )
        return
    
    keyboard = []
    for payment in payments[:10]:
        username = payment['username'] or payment['first_name']
        keyboard.append([InlineKeyboardButton(
            f"💳 {username} - {payment['plan_name']} (₹{payment['price']})",
            callback_data=f"verify_payment_{payment['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    
    await query.answer()
    await query.edit_message_text(
        f"✅ <b>Pending Verifications ({len(payments)})</b>\n\n"
        f"Click to review:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    await update.message.reply_text(
        "📢 <b>Broadcast Mode</b>\n\n"
        "Send me the message you want to broadcast to all users.\n"
        "You can send text, photos, videos, files, or polls!",
        parse_mode='HTML'
    )
    context.user_data['broadcast_mode'] = True

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "owner_panel":
        await owner_panel(update, context)
    elif data == "show_stats":
        await show_stats(update, context)
    elif data == "list_users":
        await list_users(update, context)
    elif data == "list_banned":
        await list_banned(update, context)
    elif data == "manage_plans":
        await manage_plans(update, context)
    elif data == "set_payment":
        await set_payment_info(update, context)
    elif data == "manage_auth_keys":
        await manage_auth_keys(update, context)
    elif data == "verify_payments":
        await verify_payments(update, context)
    elif data.startswith("unban_"):
        user_id = int(data.split("_")[1])
        db.unban_user(user_id)
        await query.answer("✅ User unbanned!")
        await list_banned(update, context)
    elif data.startswith("delete_plan_"):
        plan_id = int(data.split("_")[2])
        db.delete_plan(plan_id)
        await query.answer("✅ Plan deleted!")
        await manage_plans(update, context)
    elif data.startswith("revoke_key_"):
        key = data.replace("revoke_key_", "")
        db.revoke_auth_key(key)
        await query.answer("✅ Key revoked!")
        await manage_auth_keys(update, context)
    elif data.startswith("user_action_"):
        user_id = int(data.split("_")[2])
        keyboard = [
            [InlineKeyboardButton("💬 Send Message", callback_data=f"msg_user_{user_id}")],
            [InlineKeyboardButton("🚫 Ban User", callback_data=f"ban_user_{user_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="list_users")]
        ]
        await query.answer()
        await query.edit_message_text(
            f"👤 <b>User Actions</b>\n\nUser ID: {user_id}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data.startswith("ban_user_"):
        user_id = int(data.split("_")[2])
        db.ban_user(user_id)
        await query.answer("✅ User banned!")
        await list_users(update, context)
    elif data.startswith("msg_user_"):
        user_id = int(data.split("_")[2])
        context.user_data['send_to_user'] = user_id
        await query.answer()
        await query.edit_message_text(
            f"💬 Send your message for user {user_id}:"
        )
