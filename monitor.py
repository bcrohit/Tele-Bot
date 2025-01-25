import os
import hashlib
import requests
import psycopg2
from telegram import Bot
from datetime import datetime
import asyncio

from dotenv import load_dotenv
load_dotenv()

# Telegram bot credentials (replace with your actual token and chat ID)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Website to monitor (replace this with your target URL)
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"


# Initialize Telegram bot
bot = Bot(token=BOT_TOKEN)

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    """
    return psycopg2.connect(
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USERNAME"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

def initialize_database():
    """Creates a table for storing hashes if it doesn't exist."""
    conn =  get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hashes (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            hash TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_website_content(url):
    """Fetches the content of the given URL."""
    try:
        response = requests.get(url, timeout=10)  # Timeout after 10 seconds
        response.raise_for_status()  # Raise an error for HTTP errors (e.g., 404, 500)
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def calculate_hash(content):
    """Generates an MD5 hash of the given content."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def get_last_hash():
    """Retrieves the most recent hash from the database."""
    conn =  get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hash FROM hashes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None

def store_hash(hash_code):
    """Stores a new hash in the database with a timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert current timestamp and hash code into database
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    query = f"INSERT INTO hashes (timestamp, hash) VALUES ('{date}', '{hash_code}')"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

def send_telegram_message(message):
    """Sends a message via Telegram bot."""
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        print("Telegram notification sent!")
        
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

async def send_message():
    # Create an instance of the bot
    bot = Bot(token=BOT_TOKEN)
    
    # Send the message and await its completion
    message = f"Website content has changed: {URL}"
    await bot.send_message(chat_id=CHAT_ID, text=message)
    print("Message sent!")

def check_website():
    """Checks the website and sends notifications if content changes."""
    # Fetch website content
    content = get_website_content(URL)
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

if __name__ == "__main__":
    initialize_database()
    check_website()