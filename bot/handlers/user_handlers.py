import logging

from telebot import TeleBot, types
from bot.database.crud import crud
from bot.database.connector import db_connector
from bot.utils.decorators import log_message
from bot.utils.keyboards import get_main_menu_keyboard
from bot.config import Config, BotMessages


logger = logging.getLogger(__name__)


def register_user_handlers(bot: TeleBot):
    
    @bot.message_handler(commands=['start', 'help'])
    @log_message
    def handle_start(message: types.Message):
        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if user and user.is_banned:
                bot.reply_to(message, BotMessages.BANNED_MESSAGE)
                return
                
            if not user:
                user = crud.create_user(
                    session,
                    chat_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name
                )
                logger.info(f"New user registered: {user}")
            
            bot.send_message(
                message.chat.id,
                BotMessages.WELCOME_MESSAGE,
                reply_markup=get_main_menu_keyboard()
            )


    @bot.message_handler(commands=['mytickets'])
    @log_message
    def handle_my_tickets(message: types.Message):
        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if not user or user.is_banned:
                bot.reply_to(message, BotMessages.ACCESS_DENIED)
                return
                
            tickets = crud.get_user_tickets(session, user.id)
            
            if not tickets:
                bot.reply_to(message, BotMessages.NO_TICKETS)
                return
                
            response = [BotMessages.TICKETS_HEADER]
            for ticket in tickets:
                status_icon = "✓" if ticket.status == "open" else "×"
                response.append(
                    BotMessages.TICKET_ITEM.format(
                        status_icon=status_icon,
                        ticket_id=ticket.id,
                        status=ticket.status,
                        date=ticket.created_at.strftime('%d.%m.%Y %H:%M'),
                        preview=ticket.message[:50]
                    )
                )
            
            bot.send_message(
                message.chat.id,
                "\n\n".join(response),
                reply_markup=get_main_menu_keyboard()
            )


    @bot.message_handler(func=lambda m: True, content_types=['text'])
    @log_message
    def handle_text_message(message: types.Message):
        if message.reply_to_message:
            return
            
        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if not user or user.is_banned:
                bot.reply_to(message, BotMessages.ACCESS_DENIED)
                return
                
            ticket = crud.create_ticket(session, user.id, message.text)
            notify_admins_about_new_ticket(bot, ticket, user)
            
            bot.reply_to(
                message,
                BotMessages.TICKET_CREATED.format(ticket_id=ticket.id),
                reply_markup=get_main_menu_keyboard()
            )


def notify_admins_about_new_ticket(bot: TeleBot, ticket, user):
    admin_message = BotMessages.ADMIN_NOTIFICATION.format(
        ticket_id=ticket.id,
        username=user.username or 'N/A',
        user_id=user.id,
        date=ticket.created_at.strftime('%d.%m.%Y %H:%M'),
        message=ticket.message
    )
    
    admin_keyboard = types.InlineKeyboardMarkup()
    admin_keyboard.row(
        types.InlineKeyboardButton(
            text="Ответить",
            callback_data=f"reply_{ticket.id}"
        ),
        types.InlineKeyboardButton(
            text="Закрыть",
            callback_data=f"close_{ticket.id}"
        )
    )
    admin_keyboard.row(
        types.InlineKeyboardButton(
            text="Блокировать",
            callback_data=f"ban_{ticket.id}"
        )
    )
    
    for admin_id in Config.ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                admin_message,
                reply_markup=admin_keyboard
            )
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")
