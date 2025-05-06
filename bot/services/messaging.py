import logging
import time

from typing import Optional, Union, List
from telebot import TeleBot, types
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, Message
from telebot.apihelper import ApiTelegramException
from bot.database import crud
from bot.database.connector import db_connector
from bot.config import Config, BotMessages
from bot.utils.keyboards import get_admin_ticket_keyboard


logger = logging.getLogger(__name__)


class MessagingService:

    def __init__(self, bot: TeleBot):
        self.bot = bot


    def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        disable_web_page_preview: Optional[bool] = True,
        max_retries: int = 2
    ) -> Optional[Message]:
        for attempt in range(max_retries):
            try:
                return self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
            except ApiTelegramException as e:
                logger.error(f"Error sending message to {chat_id} (attempt {attempt + 1}): {e}")
                if e.error_code == 403:  # Бот заблокирован пользователем
                    self._handle_blocked_user(chat_id)
                    return None
                if attempt == max_retries - 1:
                    logger.error(f"Failed to send message after {max_retries} attempts")
                    raise


    def notify_admins(
        self,
        text: str,
        keyboard: Optional[types.InlineKeyboardMarkup] = None,
        exclude_admin_ids: Optional[List[int]] = None
    ) -> int:
        success_count = 0
        exclude_admin_ids = exclude_admin_ids or []
        
        for admin_id in set(Config.ADMIN_IDS) - set(exclude_admin_ids):
            try:
                self.send_message(admin_id, text, reply_markup=keyboard)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        return success_count


    def notify_about_new_ticket(self, ticket_id: int, user_id: int) -> int:
        with db_connector.session_scope() as session:
            ticket = crud.get_ticket(session, ticket_id)
            user = crud.get_user(session, user_id)
            
            if not ticket or not user:
                logger.error(f"Ticket {ticket_id} or user {user_id} not found")
                return 0
            
            message_text = BotMessages.ADMIN_NOTIFICATION.format(
                ticket_id=ticket.id,
                username=user.username or "N/A",
                user_id=user.id,
                date=ticket.created_at.strftime('%d.%m.%Y %H:%M'),
                message=ticket.message
            )
            
            keyboard = get_admin_ticket_keyboard(ticket.id)
            return self.notify_admins(message_text, keyboard)


    def reply_to_ticket(
        self,
        ticket_id: int,
        admin_id: int,
        reply_text: str
    ) -> bool:
        with db_connector.session_scope() as session:
            ticket = crud.get_ticket(session, ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return False
                
            user = crud.get_user(session, ticket.user_id)
            if not user or user.is_banned:
                logger.error(f"User {ticket.user_id} not found or banned")
                return False
            
            try:
                response_text = BotMessages.USER_REPLY.format(
                    ticket_id=ticket_id,
                    reply_text=reply_text
                )
                
                self.send_message(user.chat_id, response_text)
                
                crud.update_ticket(
                    session,
                    ticket_id,
                    {
                        "status": "closed",
                        "admin_id": admin_id,
                        "response": reply_text
                    }
                )
                
                crud.log_admin_action(
                    session,
                    admin_id=admin_id,
                    action="reply",
                    target_user_id=user.id,
                    details=f"Ticket #{ticket_id}"
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to reply to ticket {ticket_id}: {e}")
                return False


    def _handle_blocked_user(self, chat_id: int) -> None:
        with db_connector.session_scope() as session:
            user = crud.get_user(session, chat_id)
            if user:
                crud.update_user(session, user.id, {"is_banned": True})
                logger.info(f"User {chat_id} blocked the bot, marked as banned")


    def broadcast_message(
        self,
        text: str,
        user_ids: List[int],
        batch_size: int = 20,
        delay: float = 0.5
    ) -> dict:
        result = {'success': 0, 'failed': 0, 'blocked': 0}
        
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            for user_id in batch:
                try:
                    self.send_message(user_id, text)
                    result['success'] += 1
                except ApiTelegramException as e:
                    if e.error_code == 403:
                        result['blocked'] += 1
                        self._handle_blocked_user(user_id)
                    else:
                        result['failed'] += 1
                        logger.error(f"Failed to broadcast to {user_id}: {e}")
                except Exception as e:
                    result['failed'] += 1
                    logger.error(f"Error broadcasting to {user_id}: {e}")
            
            if i + batch_size < len(user_ids):
                time.sleep(delay)
        
        return result
