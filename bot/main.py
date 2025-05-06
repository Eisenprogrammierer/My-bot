import os
import logging

from telebot import TeleBot

from bot.database.connector import init_db, db_connector
from bot.database.models import Base

from bot.handlers import register_handlers
from bot.config import Config


def configure_logging():
    """Интерфейс настройки логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():

    logger = configure_logging()
    logger.info("Starting bot initialization...")


    with db_connector.engine.begin() as connection:
        Base.metadata.create_all(connection)

    bot_token = Config.BOT_TOKEN
    if not bot_token:
        logger.error("BOT_TOKEN not configured!")
        raise ValueError("Token must be provided")
    

    init_db(Config.DB_URL)
    
    
    bot = TeleBot(bot_token, parse_mode="HTML")
    
    
    register_handlers(bot)
    
    
    logger.info("Bot is starting...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Error occured: {str(e)}")
        raise

if __name__ == "__main__":
    main()
