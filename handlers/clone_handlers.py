from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID
import database as db

async def get_clone_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    
    if query.data == "get_clone":
        plans = db.get_all_plans()
        
        if not plans:
            await query.answer("❌ No plans available!")
            await query.edit_message_text(
                "⚠️ Clone bot feature is not available yet.\n"
                "Please contact Sam for more information."
            )
            return
        
        keyboard = []
        text = "🤖 <b>Get Your Bot Clone!</b>\n\n"
        text += "Choose a subscription plan:\n\n"
        
        for plan in plans:
            text += f"💳 <b>{plan['name']}</b>\n"
            text += f"   Price: ₹{plan['price']}\n"
            text += f"   Duration: {plan['days']} days\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"💎 {plan['name']} - ₹{plan['price']}",
                callback_data=f"buy_plan_{plan['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        await query.answer()
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("buy_plan_"):
        plan_id = int(query.data.split("_")[2])
        payment_info = db.get_payment_info()
        
        if not payment_info:
            await query.answer("❌ Payment not configured!")
            return
        
        context.user_data['selected_plan'] = plan_id
        
        keyboard = [[InlineKeyboardButton("✅ Paid & Verify", callback_data="paid_verify")]]
        
        await query.answer()
        await context.bot.send_photo(
            chat_id=user.id,
            photo=payment_info['qr_code_file_id'],
            caption=f"💰 <b>Payment Instructions</b>\n\n"
                    f"UPI ID: <code>{payment_info['upi_id']}</code>\n\n"
                    f"1. Scan QR or use UPI ID\n"
                    f"2. Make payment\n"
                    f"3. Click 'Paid & Verify' below\n"
                    f"4. Upload payment screenshot",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "paid_verify":
        await query.answer()
        await query.edit_message_caption(
            caption="📸 <b>Upload Payment Screenshot</b>\n\n"
                    "Send me the screenshot of your payment",
            parse_mode='HTML'
        )
        context.user_data['awaiting_payment_screenshot'] = True
    
    elif query.data.startswith("verify_payment_"):
        if user.id != OWNER_ID:
            await query.answer("❌ Access denied!")
            return
        
        payment_id = int(query.data.split("_")[2])
        payment = db.get_pending_payments()
        payment = [p for p in payment if p['id'] == payment_id][0]
        
        await query.answer()
        await context.bot.send_photo(
            chat_id=user.id,
            photo=payment['screenshot_file_id'],
            caption=f"💳 <b>Payment Verification</b>\n\n"
                    f"User: {payment['first_name']} (@{payment['username']})\n"
                    f"Plan: {payment['plan_name']}\n"
                    f"Amount: ₹{payment['price']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data="verify_payments")]
            ])
        )
    
    elif query.data.startswith("approve_payment_"):
        if user.id != OWNER_ID:
            await query.answer("❌ Access denied!")
            return
        
        payment_id = int(query.data.split("_")[2])
        payments = db.get_pending_payments()
        payment = [p for p in payments if p['id'] == payment_id][0]
        
        # Create auth key
        auth_key = db.create_auth_key(payment['user_id'], payment['plan_id'])
        db.approve_payment(payment_id)
        
        # Send auth key to user
        await context.bot.send_message(
            chat_id=payment['user_id'],
            text=f"✅ <b>Payment Approved!</b>\n\n"
                 f"Your Auth Key:\n<code>{auth_key}</code>\n\n"
                 f"Now create a new bot with @BotFather and send me the bot token to activate your clone bot!",
            parse_mode='HTML'
        )
        
        await query.answer("✅ Payment approved!")
        await query.edit_message_caption(
            caption=f"✅ Payment approved!\n\nAuth key sent to user.",
            parse_mode='HTML'
        )
        
        context.user_data['awaiting_bot_token'] = auth_key

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if context.user_data.get('awaiting_payment_screenshot') and update.message.photo:
        plan_id = context.user_data.get('selected_plan')
        file_id = update.message.photo[-1].file_id
        
        payment_id = db.add_payment_request(user.id, plan_id, file_id)
        
        await update.message.reply_text(
            "✅ <b>Screenshot Received!</b>\n\n"
            "Your payment is under review.\n"
            "You'll receive your auth key once Sam verifies the payment! ⏳",
            parse_mode='HTML'
        )
        
        # Notify owner
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💳 <b>New Payment Request</b>\n\n"
                 f"From: {user.first_name} (@{user.username})\n"
                 f"Payment ID: {payment_id}\n\n"
                 f"Use /verify to review",
            parse_mode='HTML'
        )
        
        context.user_data['awaiting_payment_screenshot'] = False
        context.user_data['selected_plan'] = None

async def handle_bot_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    auth_key = context.user_data.get('awaiting_bot_token')
    
    if auth_key and update.message.text.count(':') == 1:
        bot_token = update.message.text.strip()
        
        if db.activate_auth_key(auth_key, bot_token):
            await update.message.reply_text(
                "�� <b>Clone Bot Activated!</b>\n\n"
                "Your bot is now live! Start using it to communicate with your users.\n\n"
                "Your bot has basic send/receive features.\n"
                "Happy chatting! 🚀",
                parse_mode='HTML'
            )
            context.user_data['awaiting_bot_token'] = None
        else:
            await update.message.reply_text("❌ Invalid auth key!")
