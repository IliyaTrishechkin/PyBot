import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    info = await bot.get_webhook_info()
    if info.url:
        print("🚨 Вебхук усе ще встановлено за адресою:", info.url)
    else:
        print("✅ Вебхук видалено, переключаємося на опитування.")

if __name__ == "__main__":
    asyncio.run(main())