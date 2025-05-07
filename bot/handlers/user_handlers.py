import logging

from telebot import TeleBot, types
from bot.database.crud import crud
from bot.database.connector import db_connector
from bot.utils.decorators import log_message
from bot.utils.keyboards import get_language_keyboard, get_main_menu_keyboard
from bot.config import Config, BotMessages, Languages


logger = logging.getLogger(__name__)


def register_user_handlers(bot: TeleBot):

    def send_localized_message(chat_id: int, message_key: str, **kwargs):
        lang = get_user_language(chat_id)
        try:
            message = getattr(BotMessages, message_key)[lang].format(**kwargs)
            bot.send_message(chat_id, message)
        except (KeyError, AttributeError) as e:
            logger.error(f"Translation error for {message_key} in {lang}: {e}")
            fallback = getattr(BotMessages, message_key).get(Config.DEFAULT_LANGUAGE, "Error")
            bot.send_message(chat_id, fallback.format(**kwargs))


    @bot.message_handler(commands=['start', 'help'])
    @log_message
    def handle_start(message: types.Message):
        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if user and user.is_banned:
                send_localized_message(message.chat.id, 'BANNED_MESSAGE')
                return

            if not user:
                user = crud.create_user(
                    session,
                    chat_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    language=detect_language(message)
                )
                logger.info(f"New user registered: {user}")

                bot.send_message(
                    message.chat.id,
                    BotMessages.LANGUAGE_SELECT[user.language],
                    reply_markup=get_language_keyboard()
                )
            else:
                send_localized_message(message.chat.id, 'WELCOME_MESSAGE')


    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def handle_language_selection(call: types.CallbackQuery):
        lang = call.data.split('_')[1]
        if lang not in {Languages.EN, Languages.DE, Languages.RU}:
            lang = Config.DEFAULT_LANGUAGE

        with db_connector.session_scope() as session:
            if not crud.update_user(session, call.from_user.id, {"language": lang}):
                logger.error(f"Failed to update language for user {call.from_user.id}")
                bot.answer_callback_query(call.id, "Language update failed")
                return

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )

        send_localized_message(
            call.message.chat.id,
            'WELCOME_MESSAGE',
            reply_markup=get_main_menu_keyboard(lang)
        )
        bot.answer_callback_query(call.id)


    @bot.message_handler(commands=['mytickets'])
    @log_message
    def handle_my_tickets(message: types.Message):
        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if not user or user.is_banned:
                send_localized_message(message.chat.id, 'ACCESS_DENIED')
                return

            tickets = crud.get_user_tickets(session, user.id)
            if not tickets:
                send_localized_message(message.chat.id, 'NO_TICKETS')
                return

            response = [BotMessages.TICKETS_HEADER[user.language]]
            
            for ticket in tickets:
                status_icon = "✓" if ticket.status == "open" else "×"
                response.append(
                    BotMessages.TICKET_ITEM[user.language].format(
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
                reply_markup=get_main_menu_keyboard(user.language)
            )


    @bot.message_handler(func=lambda m: True, content_types=['text'])
    @log_message
    def handle_text_message(message: types.Message):
        if message.reply_to_message:
            return

        with db_connector.session_scope() as session:
            user = crud.get_user(session, message.from_user.id)
            
            if not user or user.is_banned:
                send_localized_message(message.chat.id, 'ACCESS_DENIED')
                return

            ticket = crud.create_ticket(session, user.id, message.text)
            notify_admins_about_new_ticket(bot, ticket, user)
            
            send_localized_message(
                message.chat.id,
                'TICKET_CREATED',
                ticket_id=ticket.id
            )


    def detect_language(message: types.Message) -> str:
        lang_code = message.from_user.language_code
        if lang_code in {'ru', 'be', 'uk', 'kk'}:
            return Languages.RU
        elif lang_code in {'de', 'at', 'ch'}:
            return Languages.DE
        return Config.DEFAULT_LANGUAGE

    def notify_admins_about_new_ticket(bot: TeleBot, ticket, user):
        lang = user.language
        
        admin_message = BotMessages.ADMIN_NOTIFICATION[lang].format(
            ticket_id=ticket.id,
            username=user.username or 'N/A',
            user_id=user.id,
            date=ticket.created_at.strftime('%d.%m.%Y %H:%M'),
            message=ticket.message
        )

        admin_keyboard = types.InlineKeyboardMarkup()
        admin_keyboard.row(
            types.InlineKeyboardButton(
                text="Ответить" if lang == Languages.RU else "Reply" if lang == Languages.EN else "Antworten",
                callback_data=f"reply_{ticket.id}"
            ),
            types.InlineKeyboardButton(
                text="Закрыть" if lang == Languages.RU else "Close" if lang == Languages.EN else "Schließen",
                callback_data=f"close_{ticket.id}"
            )
        )
        admin_keyboard.row(
            types.InlineKeyboardButton(
                text="Блокировать" if lang == Languages.RU else "Ban" if lang == Languages.EN else "Sperren",
                callback_data=f"ban_{ticket.id}"
            )
        )

        for admin_id in Config.ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_message, reply_markup=admin_keyboard)
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
