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

        # Get the current date and format it
        today_date = datetime.now()
        formatted_date = today_date.strftime("%A (%d-%m-%Y)")  # e.g., "Wednesday (09-10-2024)"

        # Prepare the new aired shows list
        new_aired_titles = {i["title"] for i in aniContent if i["aired"]}

        sch_list = ""
        text = f"📅 Schedule for {formatted_date}\n\n"  # Include the formatted date
        for i in aniContent:
            aired_icon = "✅ " if i["aired"] else ""
            title = i["title"]
            time = i["time"]
            sch_list += f"""[`{time}`] - 📌 ___{title}___ {aired_icon}\n\n"""

        text += sch_list
        text += """___⏰ Current TimeZone :___ `IST (UTC +5:30)`"""

        # If we have an existing message, update it
        if last_message_id:
            await client.edit_message(MAIN_CHANNEL, last_message_id, text)
            logger.info("Schedule message updated successfully.")
        else:
            # Step 1: Send the image with the caption
            message = await client.send_file(MAIN_CHANNEL, 'schedule_image.jpg', caption=text)
            last_message_id = message.id  # Store the last message ID
            logger.info("Schedule message sent successfully.")

            # Step 2: Pin the message
            pinned_message = await client(PinMessage(
                channel=MAIN_CHANNEL,
                id=message.id,
                silent=True  # Silent pin, no notification
            ))

            # Step 3: Delete the service message that appears when pinning
            await client.delete_messages(MAIN_CHANNEL, pinned_message.id)

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
