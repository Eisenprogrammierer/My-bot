import logging

from telebot import TeleBot, types
from bot.database.connector import db_connector
from bot.services.admin_actions import AdminActions
from bot.services.messaging import MessagingService
from bot.utils.decorators import access_check
from bot.utils.keyboards import (
    get_admin_main_keyboard,
    get_admin_ticket_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard
)
from bot.config import BotMessages


logger = logging.getLogger(__name__)


def register_admin_handlers(bot: TeleBot):
    admin_actions = AdminActions(bot)
    messaging = MessagingService(bot)

    admin_states = {}


    @bot.message_handler(commands=['admin'])
    @access_check(is_admin=True)
    def handle_admin_panel(message: types.Message):
        admin_actions.show_admin_panel(message.from_user.id)


    @bot.callback_query_handler(func=lambda call: call.data.startswith('ban_'))
    @access_check(is_admin=True)
    def handle_ban_user(call: types.CallbackQuery):
        ticket_id = int(call.data.split('_')[1])
        
        with db_connector.session_scope() as session:
            ticket = crud.get_ticket(session, ticket_id)
            if not ticket:
                bot.answer_callback_query(call.id, "Обращение не найдено")
                return

            admin_states[call.from_user.id] = {
                'action': 'ban',
                'user_id': ticket.user_id,
                'ticket_id': ticket_id
            }

            bot.send_message(
                call.from_user.id,
                f"⚠️ Подтвердите блокировку пользователя ID: {ticket.user_id}",
                reply_markup=get_confirmation_keyboard()
            )
            bot.answer_callback_query(call.id)


    @bot.callback_query_handler(func=lambda call: call.data.startswith('close_'))
    @access_check(is_admin=True)
    def handle_close_ticket(call: types.CallbackQuery):
        ticket_id = int(call.data.split('_')[1])
        
        if admin_actions.close_ticket(call.from_user.id, ticket_id):
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            bot.answer_callback_query(call.id, "Обращение закрыто")
        else:
            bot.answer_callback_query(call.id, "Ошибка закрытия обращения")


    @bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
    @access_check(is_admin=True)
    def handle_reply_to_ticket(call: types.CallbackQuery):
        ticket_id = int(call.data.split('_')[1])
        
        admin_states[call.from_user.id] = {
            'action': 'reply',
            'ticket_id': ticket_id
        }

        bot.send_message(
            call.from_user.id,
            "✍️ Введите ваш ответ пользователю:",
            reply_markup=get_cancel_keyboard()
        )
        bot.answer_callback_query(call.id)


    @bot.message_handler(func=lambda m: m.text == "❌ Отмена" and m.from_user.id in admin_states)
    @access_check(is_admin=True)
    def handle_cancel_action(message: types.Message):
        if message.from_user.id in admin_states:
            del admin_states[message.from_user.id]
        bot.send_message(
            message.chat.id,
            "Действие отменено",
            reply_markup=get_admin_main_keyboard()
        )


    @bot.callback_query_handler(func=lambda call: call.data in ['confirm', 'cancel'])
    @access_check(is_admin=True)
    def handle_confirmation(call: types.CallbackQuery):
        user_state = admin_states.get(call.from_user.id, {})
        
        if call.data == 'confirm' and user_state:
            if user_state['action'] == 'ban':
                admin_actions.ban_user(
                    admin_id=call.from_user.id,
                    user_id=user_state['user_id'],
                    reason=f"По обращению #{user_state['ticket_id']}"
                )
                bot.send_message(
                    call.from_user.id,
                    f"Пользователь {user_state['user_id']} заблокирован",
                    reply_markup=get_admin_main_keyboard()
                )
            
            del admin_states[call.from_user.id]
        
        elif call.data == 'cancel':
            bot.send_message(
                call.from_user.id,
                "Действие отменено",
                reply_markup=get_admin_main_keyboard()
            )
            if call.from_user.id in admin_states:
                del admin_states[call.from_user.id]
        
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


    @bot.message_handler(func=lambda m: m.from_user.id in admin_states and admin_states[m.from_user.id]['action'] == 'reply')
    @access_check(is_admin=True)
    def handle_admin_reply(message: types.Message):
        user_state = admin_states.get(message.from_user.id)
        if not user_state:
            return

        ticket_id = user_state['ticket_id']
        del admin_states[message.from_user.id]
        
        if messaging.reply_to_ticket(ticket_id, message.from_user.id, message.text):
            bot.send_message(
                message.chat.id,
                "✅ Ответ отправлен пользователю",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Не удалось отправить ответ",
                reply_markup=get_admin_main_keyboard()
            )


    @bot.message_handler(func=lambda m: m.text in ["📊 Статистика", "📨 Все обращения", "👥 Пользователи"])
    @access_check(is_admin=True)
    def handle_admin_commands(message: types.Message):
        if message.text == "📊 Статистика":
            stats = admin_actions.get_system_stats()
            response = (
                "📊 <b>Статистика системы</b>\n\n"
                f"👥 Пользователей: {stats['total_users']}\n"
                f"⛔ Заблокировано: {stats['banned_users']}\n"
                f"📨 Обращений: {stats['total_tickets']}\n"
                f"🟢 Открытых: {stats['open_tickets']}"
            )
            bot.send_message(message.chat.id, response)
        
        elif message.text == "📨 Все обращения":
            with db_connector.session_scope() as session:
                tickets = crud.get_open_tickets(session)
                if not tickets:
                    bot.send_message(message.chat.id, "Нет открытых обращений")
                    return
                
                response = ["📂 Открытые обращения:"]
                for ticket in tickets[:10]:
                    response.append(
                        f"#{ticket.id} от пользователя {ticket.user_id}\n"
                        f"📅 {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                        f"📝 {ticket.message[:50]}..."
                    )
                
                bot.send_message(
                    message.chat.id,
                    "\n\n".join(response),
                    reply_markup=get_admin_main_keyboard()
                )
        
        elif message.text == "👥 Пользователи":
            bot.send_message(
                message.chat.id,
                "Введите ID пользователя или @username для поиска:",
                reply_markup=get_cancel_keyboard()
            )
            admin_states[message.from_user.id] = {'action': 'user_search'}


    @bot.message_handler(func=lambda m: m.from_user.id in admin_states and admin_states[m.from_user.id]['action'] == 'user_search')
    @access_check(is_admin=True)
    def handle_user_search(message: types.Message):
        search_query = message.text.strip()
        with db_connector.session_scope() as session:
            try:
                user_id = int(search_query)
                user = crud.get_user(session, user_id)
                if user:
                    stats = admin_actions.get_user_stats(user.id)
                    response = (
                        f"👤 <b>Пользователь ID: {user.id}</b>\n"
                        f"👁‍🗨 @{user.username or 'нет'}\n"
                        f"📛 {user.first_name} {user.last_name or ''}\n"
                        f"⛔ {'Заблокирован' if user.is_banned else 'Активен'}\n\n"
                        f"📨 Обращений: {stats['total_tickets']}\n"
                        f"🟢 Открытых: {stats['open_tickets']}"
                    )
                    
                    keyboard = types.InlineKeyboardMarkup()
                    if user.is_banned:
                        keyboard.add(types.InlineKeyboardButton(
                            text="🔓 Разблокировать",
                            callback_data=f"unban_{user.id}"
                        ))
                    else:
                        keyboard.add(types.InlineKeyboardButton(
                            text="⛔ Заблокировать",
                            callback_data=f"ban_{user.id}"
                        ))
                    
                    bot.send_message(
                        message.chat.id,
                        response,
                        reply_markup=keyboard
                    )
                    del admin_states[message.from_user.id]
                    return
            except ValueError:
                pass
            
            username = search_query.lstrip('@')
            users = session.query(crud.User).filter(
                crud.User.username.ilike(f"%{username}%")
            ).limit(5).all()
            
            if not users:
                bot.send_message(
                    message.chat.id,
                    "Пользователи не найдены",
                    reply_markup=get_admin_main_keyboard()
                )
                return
            
            response = ["🔍 Результаты поиска:"]
            for user in users:
                response.append(
                    f"ID: {user.id} | @{user.username or 'нет'}\n"
                    f"{user.first_name} | "
                    f"{'⛔' if user.is_banned else '🟢'}"
                )
            
            bot.send_message(
                message.chat.id,
                "\n\n".join(response),
                reply_markup=get_admin_main_keyboard()
            )
        del admin_states[message.from_user.id]


    @bot.callback_query_handler(func=lambda call: call.data.startswith('unban_'))
    @access_check(is_admin=True)
    def handle_unban_user(call: types.CallbackQuery):
        user_id = int(call.data.split('_')[1])
        if admin_actions.unban_user(call.from_user.id, user_id):
            bot.answer_callback_query(call.id, "Пользователь разблокирован")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка разблокировки")
