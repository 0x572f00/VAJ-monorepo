import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.user_handlers import user_handlers
from app.admin_handlers import admin_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    logger.info("Starting bot...")
    
    dp.include_router(user_handlers)
    dp.include_router(admin_handlers)
    
    await dp.start_polling(bot)
    logger.info("Bot started successfully")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
