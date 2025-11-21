import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
DATABASE_URL = os.getenv('DATABASE_URL', 'bot_database.db')

# Bot settings
OWNER_NAME = "Sam"
GREETINGS = [
    "Thanks for reaching out! 💫 Sam will get back to you soon!",
    "Message received! ✨ Sam will respond shortly!",
    "Got it! 🌟 Sam will reply as soon as possible!",
    "Your message is on its way to Sam! 🚀",
    "Message delivered! 📬 Sam will be in touch soon!",
    "Thanks! 💬 Sam will check this out!",
]
