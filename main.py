import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, OWNER_ID
from handlers import owner_handlers, user_handlers, clone_handlers
from database import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def handle_callback(update, context):
    query = update.callback_query
    data = query.data
    
    # Route to appropriate handler
    if data in ["get_clone", "paid_verify", "main_menu"] or data.startswith(("buy_plan_", "verify_payment_", "approve_payment_", "reject_payment_")):
        await clone_handlers.get_clone_bot(update, context)
    elif data == "send_to_owner":
        await query.answer()
        await query.edit_message_text("💬 Send me your message and I'll forward it to Sam!")
    else:
        await owner_handlers.button_callback(update, context)

async def handle_all_messages(update, context):
    user = update.effective_user
    
    # Check for payment screenshot
    if context.user_data.get('awaiting_payment_screenshot') and update.message.photo:
        await clone_handlers.handle_payment_screenshot(update, context)
        return
    
    # Check for bot token
    if context.user_data.get('awaiting_bot_token') and update.message.text:
        await clone_handlers.handle_bot_token(update, context)
        return
    
    # Check for owner setting UPI after QR
    if user.id == OWNER_ID and context.user_data.get('payment_qr') and update.message.text:
        import database as db
        db.set_payment_info(context.user_data['payment_qr'], update.message.text.strip())
        await update.message.reply_text("✅ Payment info saved!")
        context.user_data['payment_qr'] = None
        context.user_data['awaiting_payment_info'] = False
        return
    
    # Regular message handling
    if update.message.text:
        await user_handlers.handle_message(update, context)
    else:
        await user_handlers.handle_media(update, context)

def main():
    """Start the bot."""
    init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Owner commands
    application.add_handler(CommandHandler("start", owner_handlers.start_command))
    application.add_handler(CommandHandler("panel", owner_handlers.owner_panel))
    application.add_handler(CommandHandler("stats", owner_handlers.show_stats))
    application.add_handler(CommandHandler("broadcast", owner_handlers.broadcast_command))
    application.add_handler(CommandHandler("users", owner_handlers.list_users))
    application.add_handler(CommandHandler("banned", owner_handlers.list_banned))
    application.add_handler(CommandHandler("plans", owner_handlers.manage_plans))
    application.add_handler(CommandHandler("payment", owner_handlers.set_payment_info))
    application.add_handler(CommandHandler("authkeys", owner_handlers.manage_auth_keys))
    application.add_handler(CommandHandler("verify", owner_handlers.verify_payments))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        handle_all_messages
    ))
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
