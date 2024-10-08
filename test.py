import asyncio
from json import loads as jloads
from aiohttp import ClientSession
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Replace with your own values
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID (e.g., '@your_channel')
MESSAGE_ID = 2  # Message ID to update

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def update_schedule():
    """Fetch and update today's anime schedule."""
    try:
        async with ClientSession() as ses:
            res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
            aniContent = jloads(await res.text())["schedule"]

        sch_list = ""
        text = "<b>📆 Today's Schedule</b>\n\n"
        for i in aniContent:
            aired_icon = "✅ " if i["aired"] else ""
            title = i["title"]
            time = i["time"]
            sch_list += f"""[<code>{time}</code>] - 📌 <b>{aired_icon}{title}</b>\n\n"""

        text += sch_list
        text += """<b>⏰ Current TimeZone :</b> <code>IST (UTC +5:30)</code>"""

        # Update the existing message with the provided message ID
        await client.edit_message(MAIN_CHANNEL, MESSAGE_ID, text)

    except Exception as err:
        print(f"Error: {str(err)}")

async def schedule_updates():
    """Schedule the updates every 5 minutes."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_schedule, 'interval', minutes=5)  # Check every 5 minutes
    scheduler.start()

async def main():
    """Main function to run the bot."""
    await update_schedule()  # Send the schedule when the bot starts
    await schedule_updates()   # Start the scheduler
    await client.run_until_disconnected()  # Run the client until disconnected

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
