import os
import re
from flask import Flask, request
import telegram
import asyncio
from monitor import get_website_content, calculate_hash, get_last_hash, store_hash


global bot
global TOKEN
global chat_id
global URL
TOKEN = os.environ.get("BOT_TOKEN")
chat_id = os.environ.get("CHAT_ID")
hash_url = os.environ.get("HASH_URL")
heroku_url = os.environ.get("URL")

bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

async def send_message(message):    
    # Send the message and await its completion
    # message = f"Website content has changed: {URL}"
    await bot.send_message(chat_id=chat_id, text=message)
    print("Message sent!")

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    """Checks the website and sends notifications if content changes."""
    # Fetch website content
    content = get_website_content(hash_url)
    if content is None:
        print("Error fetching website content. Skipping and retrying later.")
        return

    # Calculate the current hash of the website content
    current_hash = calculate_hash(content)
    print(f"Current hash: {current_hash}")

    # Get the last stored hash
    last_hash = get_last_hash()
    print(f"Last hash: {last_hash}")

    # Check if the content has changed
    if last_hash != current_hash:
        print("Website content has changed!")
        asyncio.run(send_message())
        store_hash(current_hash)
    else:
        print("No changes detected.")
    
    return 'ok'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
   s = bot.setWebhook('{URL}{HOOK}'.format(URL=heroku_url, HOOK=TOKEN))
   if s:
       return "webhook setup ok"
   else:
       return "webhook setup failed"

@app.route('/')
def index():
   return '.'


if __name__ == '__main__':
   app.run(threaded=True)