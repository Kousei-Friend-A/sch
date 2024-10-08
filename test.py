import asyncio
import logging
from json import loads as jloads
from aiohttp import ClientSession
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your own values
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID (e.g., '@your_channel')

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

last_message_id = None  # Variable to store the last message ID

async def fetch_schedule():
    """Fetch today's anime schedule from the API."""
    async with ClientSession() as ses:
        res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
        return jloads(await res.text())["schedule"]

async def delete_previous_schedule():
    """Delete the previous schedule message if it exists."""
    global last_message_id
    if last_message_id is not None:
        try:
            await app.delete_messages(MAIN_CHANNEL, last_message_id)
            logger.info("Deleted previous schedule message.")
        except Exception as e:
            logger.error(f"Error deleting previous message: {str(e)}")

async def update_schedule():
    """Fetch and send today's anime schedule."""
    global last_message_id
    try:
        logger.info("Updating schedule...")
        await delete_previous_schedule()  # Delete previous schedule message

        aniContent = await fetch_schedule()
        sch_list = ""
        text = "<b>📆 Today's Schedule</b>\n\n"
        for i in aniContent:
            aired_icon = "✅ " if i["aired"] else ""
            title = i["title"]
            time = i["time"]
            sch_list += f"""[<code>{time}</code>] - 📌 <b>{aired_icon}{title}</b>\n\n"""

        text += sch_list
        text += """<b>⏰ Current TimeZone :</b> <code>IST (UTC +5:30)</code>"""

        # Send the new schedule message
        message = await app.send_message(MAIN_CHANNEL, text)
        last_message_id = message.message_id  # Store the last message ID
        logger.info("Schedule updated successfully.")

    except Exception as err:
        logger.error(f"Error while updating schedule: {str(err)}")

async def schedule_updates():
    """Schedule the updates for every 5 minutes and daily at 12:30 AM."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_schedule, 'interval', minutes=5)  # Check every 5 minutes
    scheduler.add_job(update_schedule, 'cron', hour=23, minute=5)  # Check every day at 11:00 PM
    scheduler.start()
    logger.info("Scheduler started.")

async def main():
    """Main function to run the bot."""
    await schedule_updates()  # Start the scheduler
    await app.start()  # Start the Pyrogram client
    logger.info("Bot started and running.")
    await asyncio.Future()  # Keep the bot running indefinitely

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
