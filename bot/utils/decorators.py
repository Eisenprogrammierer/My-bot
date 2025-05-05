import functools
import logging

from typing import Callable, Any
from telebot import types
from bot.database import crud
from bot.database.connector import db_connector
from bot.config import Config


logger = logging.getLogger(__name__)


def log_message(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(message: types.Message, *args, **kwargs) -> Any:
        logger.info(
            f"Incoming message | User: {message.from_user.id} "
            f"(@{message.from_user.username or 'no_username'}) | "
            f"Text: {message.text or 'no_text'}"
        )
        return func(message, *args, **kwargs)
    return wrapper


def access_check(is_admin: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(message: types.Message, *args, **kwargs) -> Any:
            with db_connector.session_scope() as session:
                user = crud.get_user(session, message.from_user.id)
                
                if user and user.is_banned:
                    logger.warning(
                        f"Blocked user tried to access: {message.from_user.id}"
                    )
                    return None
                
                # Проверка прав администратора
                if is_admin and message.from_user.id not in Config.ADMIN_IDS:
                    logger.warning(
                        f"Unauthorized admin access attempt: {message.from_user.id}"
                    )
                    return None
            
            return func(message, *args, **kwargs)
        return wrapper
    return decorator


def database_session(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with db_connector.session_scope() as session:
            try:
                if 'session' not in kwargs:
                    kwargs['session'] = session
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {str(e)}")
                raise
    return wrapper


def error_handler(bot_instance=None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(message: types.Message, *args, **kwargs) -> Any:
            try:
                return func(message, *args, **kwargs)
            except Exception as e:
                logger.critical(
                    f"Error in handler {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if bot_instance:
                    try:
                        bot_instance.reply_to(
                            message,
                            "⚠️ Произошла ошибка при обработке запроса. "
                            "Администратор уже уведомлен."
                        )
                        # Уведомление админов
                        for admin_id in Config.ADMIN_IDS:
                            bot_instance.send_message(
                                admin_id,
                                f"🚨 Ошибка в обработчике {func.__name__}:\n{str(e)}"
                            )
                    except Exception as bot_error:
                        logger.error(f"Failed to send error message: {bot_error}")
        return wrapper
    return decorator


def validate_message_length(max_length: int = 2000) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(message: types.Message, *args, **kwargs) -> Any:
            if len(message.text or '') > max_length:
                logger.warning(
                    f"Message too long from {message.from_user.id}: "
                    f"{len(message.text)} chars"
                )
                bot_instance = args[0] if args else kwargs.get('bot')
                if bot_instance:
                    bot_instance.reply_to(
                        message,
                        f"❌ Сообщение слишком длинное (максимум {max_length} символов)"
                    )
                return None
            return func(message, *args, **kwargs)
        return wrapper
    return decorator
