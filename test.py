import asyncio
from json import loads as jloads
from aiohttp import ClientSession
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Replace with your own values
API_ID = 8143727  # Your API ID
API_HASH = 'e2e9b22c6522465b62d8445840a526b1'  # Your API Hash
BOT_TOKEN = '7755562653:AAEG4-_HOKL9i5nUI0XPZaLMbZXMYtKB4Jo'  # Your Bot Token
MAIN_CHANNEL = '@animeencodetest'  # Your Channel ID (e.g., '@your_channel')

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def fetch_schedule():
    """Fetch today's anime schedule from the API."""
    async with ClientSession() as ses:
        res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
        return jloads(await res.text())["schedule"]

async def delete_previous_schedule():
    """Delete the previous schedule message if it exists."""
    async for message in app.get_chat_history(MAIN_CHANNEL, limit=30):
        if "⏰ Current TimeZone :" in message.text:  # Check for the timezone text
            await app.delete_messages(MAIN_CHANNEL, message.message_id)
            break

async def update_schedule():
    """Fetch and send today's anime schedule."""
    try:
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
        await app.send_message(MAIN_CHANNEL, text)

    except Exception as err:
        print(f"Error: {str(err)}")

async def schedule_updates():
    """Schedule the updates for every 5 minutes and daily at 12:30 AM."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_schedule, 'interval', minutes=5)  # Check every 5 minutes
    scheduler.add_job(update_schedule, 'cron', hour=0, minute=30)  # Check every day at 12:30 AM
    scheduler.start()

async def main():
    """Main function to run the bot."""
    await schedule_updates()  # Start the scheduler
    await app.start()  # Start the Pyrogram client
    await asyncio.Future()  # Keep the bot running indefinitely

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
