import asyncio
import logging
import json
from aiohttp import ClientSession
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your own values
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID (e.g., '@your_channel')

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

last_message_id = None  # Variable to store the last message ID
last_aired_titles = set()  # Set to store last aired titles

async def fetch_schedule():
    """Fetch today's anime schedule from the API."""
    async with ClientSession() as ses:
        res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
        return json.loads(await res.text())["schedule"]

async def update_schedule():
    """Fetch and update today's anime schedule."""
    global last_message_id, last_aired_titles
    try:
        logger.info("Updating schedule...")
        
        aniContent = await fetch_schedule()
        
        # Prepare the new aired shows list
        new_aired_titles = {i["title"] for i in aniContent if i["aired"]}
        
        sch_list = ""
        text = "<b>📆 Today's Schedule</b>\n\n"
        for i in aniContent:
            aired_icon = "✅ " if i["aired"] else ""
            title = i["title"]
            time = i["time"]
            sch_list += f"""[`{time}`] - 📌 __{title}__ {aired_icon}\n\n"""

        text += sch_list
        text += """__⏰ Current TimeZone :__ `IST (UTC +5:30)`"""

        # If we have an existing message, update it
        if last_message_id:
            await client.edit_message(MAIN_CHANNEL, last_message_id, text)
            logger.info("Schedule message updated successfully.")
        else:
            # Send the new schedule message if no message exists
            message = await client.send_message(MAIN_CHANNEL, text)
            last_message_id = message.id  # Store the last message ID
            logger.info("Schedule message sent successfully.")

        # Update last aired titles
        last_aired_titles = new_aired_titles

    except Exception as err:
        logger.error(f"Error while updating schedule: {str(err)}")

async def daily_schedule_update():
    """Delete previous schedule message and send the new schedule every 24 hours."""
    global last_message_id
    try:
        if last_message_id is not None:
            await client.delete_messages(MAIN_CHANNEL, last_message_id)
            logger.info("Deleted previous schedule message.")

        await update_schedule()  # Update the schedule message after deletion

    except Exception as err:
        logger.error(f"Error during daily schedule update: {str(err)}")

async def schedule_updates():
    """Schedule the updates for every 5 minutes and daily."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_schedule, 'interval', minutes=5)  # Check every 5 minutes
    scheduler.add_job(daily_schedule_update, 'cron', hour=8, minute=45)  # Check every day at midnight
    scheduler.start()
    logger.info("Scheduler started.")

async def main():
    """Main function to run the bot."""
    await schedule_updates()  # Start the scheduler
    await client.run_until_disconnected()  # Run the client until disconnected

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
