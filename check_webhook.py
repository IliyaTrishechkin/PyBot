import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from telegram import Bot

load_dotenv(Path(__file__).parent/'.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook()
    info = await bot.get_webhook_info()
    print("Webhook URL:", info.url)

if __name__ == "__main__":
    asyncio.run(main())
