# Telegram Reply Bot with Clone Feature

A powerful Telegram bot that enables communication between owner and users, with a unique bot cloning subscription system.

## Features

### For Owner (Sam)
- 👥 View active users list with clickable profiles
- 🚫 Ban/unban users
- 💬 Send messages to individual users
- 📢 Broadcast messages (text, images, videos, files, polls)
- 📊 Detailed statistics dashboard
- 💳 Manage subscription plans
- 💰 Set payment QR code and UPI ID
- ✅ Verify user payments
- 🔑 Manage and revoke auth keys

### For Regular Users
- 📩 Send messages to Sam in any format
- 🤖 Purchase bot clone subscriptions
- 💳 Multiple subscription plans (customizable by owner)
- 📸 Payment verification system

### Bot Clone System
- Users can purchase bot clones with subscription plans
- Clone bots have basic send/receive message features
- Auth key system for activation
- Automatic expiry management

## Deployment on Northflank

### Prerequisites
1. Northflank account (free tier available)
2. Telegram bot token from @BotFather
3. Your Telegram user ID

### Setup Steps

1. **Fork/Clone this repository**
   ```bash
   git clone https://github.com/frsammm1/northflankReplyBot.git
   cd northflankReplyBot
   ```

2. **Create a new service on Northflank**
   - Go to Northflank dashboard
   - Click "Create Service"
   - Select "Combined" service type
   - Connect your GitHub repository

3. **Configure Environment Variables**
   Add these environment variables in Northflank:
   - `BOT_TOKEN`: Your Telegram bot token
   - `OWNER_ID`: Your Telegram user ID

4. **Deploy Settings**
   - Build method: Dockerfile or Buildpack
   - Port: 8080 (if using web health check)
   - Start command: `python main.py`

5. **Deploy**
   - Click "Deploy Service"
   - Wait for deployment to complete

## Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your bot token and owner ID

3. **Run the bot**
   ```bash
   python main.py
   ```

## Bot Commands

### Owner Commands
- `/start` - Start the bot and show owner panel
- `/panel` - Open owner dashboard
- `/stats` - View detailed statistics
- `/broadcast` - Start broadcast mode
- `/users` - List all active users
- `/banned` - List banned users
- `/plans` - Manage subscription plans
- `/payment` - Set payment information
- `/authkeys` - Manage auth keys
- `/verify` - Verify pending payments

### User Commands
- `/start` - Start the bot and see options

## Database

The bot uses SQLite database with the following tables:
- `users` - User information
- `subscription_plans` - Available subscription plans
- `auth_keys` - Authentication keys for clone bots
- `payment_requests` - Payment verification requests
- `payment_info` - QR code and UPI information
- `messages` - Message history
- `clone_bots` - Registered clone bots

## Support

For issues or questions, contact the repository owner.

## License

MIT License
