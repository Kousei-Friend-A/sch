import asyncio
import logging
import json
import os
import signal
from datetime import datetime, timedelta
from aiohttp import ClientSession
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

LAST_MESSAGE_ID_FILE = 'last_message_id.json'

def load_last_message_id():
    """Load the last message ID from a JSON file."""
    if os.path.exists(LAST_MESSAGE_ID_FILE):
        with open(LAST_MESSAGE_ID_FILE, 'r') as f:
            data = json.load(f)
            return data.get('last_message_id', None)
    return None

def save_last_message_id(message_id):
    """Save the last message ID to a JSON file."""
    with open(LAST_MESSAGE_ID_FILE, 'w') as f:
        json.dump({'last_message_id': message_id}, f)

last_message_id = load_last_message_id()  # Load last message ID from the file
last_aired_titles = set()  # Set to store last aired titles

async def fetch_schedule():
    """Fetch today's anime schedule from the API."""
    try:
        async with ClientSession() as ses:
            res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
            res.raise_for_status()  # Raise an error for bad responses
            data = await res.json()
            return data["schedule"]
    except Exception as e:
        logger.error(f"Failed to fetch schedule: {str(e)}")
        return []

async def update_schedule():
    global last_message_id, last_aired_titles
    try:
        logger.info("Checking for schedule update...")
        aniContent = await fetch_schedule()

        today_date = datetime.now()
        formatted_date = today_date.strftime("%A (%d-%m-%Y)")

        new_aired_titles = {i["title"] for i in aniContent if i["aired"]}

        sch_list = ""
        for i in aniContent:
            title = i["title"]
            time = i["time"]
            
            # Use checkmark for aired shows and pin for upcoming ones
            aired_icon = "✅" if i["aired"] else "📌"
            
            # Format each entry with the desired look
            sch_list += f"""[`{time}`] - {aired_icon} **{title}**\n\n"""

        text = f"📅 **Schedule for {formatted_date}**\n\n{sch_list}"
        text += """**⏰ Current TimeZone :** `IST (UTC +5:30)`"""

        image_path = 'schedule_image.jpg'  # Path to your image file

        if last_message_id:
            try:
                # Update the existing message
                await client.edit_message(MAIN_CHANNEL, last_message_id, text)
                logger.info("Schedule message updated successfully.")
                # Send the image with the same caption
                await client.send_file(MAIN_CHANNEL, image_path, caption="Schedule")
                logger.info("Sent updated schedule image.")
            except Exception as edit_err:
                logger.error(f"Failed to edit message: {str(edit_err)}")
                last_message_id = None  # Reset if edit fails
        else:
            # Send the initial schedule message
            message = await client.send_message(MAIN_CHANNEL, text)
            last_message_id = message.id
            save_last_message_id(last_message_id)  # Save the message ID after sending
            logger.info("Schedule message sent successfully.")

            # Pin the message with notification
            await client.pin_message(MAIN_CHANNEL, message.id, notify=True)
            logger.info("Pinned the schedule message with notification.")

            # Now send the image with the caption
            await client.send_file(MAIN_CHANNEL, image_path, caption="Schedule")
            logger.info("Sent schedule image.")

        last_aired_titles = new_aired_titles

    except Exception as err:
        logger.error(f"Error while updating schedule: {str(err)}")

async def daily_schedule_update():
    """Delete previous schedule message and send the new schedule every day at 13:40 PM."""
    global last_message_id
    try:
        if last_message_id is not None:
            await client.delete_messages(MAIN_CHANNEL, last_message_id)
            logger.info("Deleted previous schedule message.")

        await update_schedule()  # Update the schedule message after deletion

    except Exception as err:
        logger.error(f"Error during daily schedule update: {str(err)}")

async def wait_until_schedule_time():
    """Wait until 13:40 PM to send the initial schedule."""
    now = datetime.now()
    target_time = now.replace(hour=13, minute=40, second=0, microsecond=0)

    if now > target_time:  # If it's already past the scheduled time, set to the next day
        target_time += timedelta(days=1)

    wait_time = (target_time - now).total_seconds()
    logger.info(f"Waiting for {wait_time} seconds until 13:40 PM...")
    await asyncio.sleep(wait_time)

async def schedule_updates():
    """Schedule the updates for every 5 minutes and daily at 13:40 PM."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_schedule, 'interval', minutes=5)  # Check every 5 minutes
    scheduler.add_job(daily_schedule_update, 'cron', hour=13, minute=40)  # Daily update at 13:40 PM
    scheduler.start()
    logger.info("Scheduler started.")

async def main():
    """Main function to run the bot."""
    await wait_until_schedule_time()  # Wait until 13:40 PM
    await update_schedule()  # Send the initial schedule
    await schedule_updates()  # Start the scheduler
    await client.run_until_disconnected()  # Run the client until disconnected

def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    asyncio.run(client.disconnect())
    loop.stop()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    signal.signal(signal.SIGINT, signal_handler)  # Handle interrupt signal
    loop.run_until_complete(main())
