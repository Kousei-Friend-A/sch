import asyncio
from json import loads as jloads
from aiohttp import ClientSession
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# Replace with your own values
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID (e.g., '@your_channel')

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store the last sent schedule date and message IDs
last_schedule_date = None
last_message_ids = []  # List to store message IDs

async def delete_previous_schedule():
    """Delete the previous day's schedule messages using stored IDs."""
    global last_message_ids, last_schedule_date
    if last_message_ids and last_schedule_date:
        for message_id in last_message_ids:
            try:
                await client.delete_messages(MAIN_CHANNEL, message_id)
            except Exception as e:
                print(f"Error deleting message {message_id}: {str(e)}")
    last_message_ids = []  # Clear the list after deletion
    last_schedule_date = datetime.now().date()

async def upcoming_animes():
    """Fetch and send today's anime schedule."""
    global last_message_ids
    try:
        async with ClientSession() as ses:
            res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
            aniContent = jloads(await res.text())["schedule"]

        sch_list = ""
        text = "<b>📆 Today's Schedule</b>\n\n"
        for i in aniContent:
            aired_icon = "✅ " if i["aired"] else ""  # Add checkmark if aired
            title = i["title"]  # Using original title
            time = i["time"]
            sch_list += f"[<code>{time}</code>] - 📌 <b>{aired_icon}{title}</b>\n\n"

        text += sch_list
        text += "<b>⏰ Current TimeZone :</b> <code>IST (UTC +5:30)</code>"

        # Delete previous schedule messages
        await delete_previous_schedule()
        
        # Send the new schedule message and pin it
        message = await client.send_message(MAIN_CHANNEL, text)
        await message.pin()  # Pin the message

        # Save the message ID of the sent schedule
        last_message_ids.append(message.id)

    except Exception as err:
        print(f"Error: {str(err)}")  # Print error to console for debugging

def schedule_upcoming_animes(scheduler):
    """Schedule the tasks."""
    scheduler.add_job(upcoming_animes, 'interval', minutes=5)  # Check every 5 minutes

async def main():
    """Main function to run the bot."""
    scheduler = AsyncIOScheduler()
    schedule_upcoming_animes(scheduler)  # Start the scheduler
    scheduler.start()  # Start the scheduler
    await client.run_until_disconnected()  # Run the client until disconnected

if __name__ == '__main__':
    asyncio.run(main())
