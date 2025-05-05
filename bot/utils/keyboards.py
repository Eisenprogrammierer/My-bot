from telebot import types
from bot.config import BotMessages


def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton(text="📨 Новое обращение"),
        types.KeyboardButton(text="📂 Мои обращения"),
        types.KeyboardButton(text="§ Помощь")
    ]
    keyboard.add(*buttons)
    return keyboard


def get_admin_ticket_keyboard(ticket_id: int) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            text="✉️ Ответить",
            callback_data=f"reply_{ticket_id}"
        ),
        types.InlineKeyboardButton(
            text="🔒 Закрыть",
            callback_data=f"close_{ticket_id}"
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="⛔ Блокировать",
            callback_data=f"ban_{ticket_id}"
        )
    )
    return keyboard


def get_cancel_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="❌ Отмена"))
    return keyboard


def get_confirmation_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="confirm"
        ),
        types.InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="cancel"
        )
    )
    return keyboard


def get_admin_main_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton(text="📊 Статистика"),
        types.KeyboardButton(text="📨 Все обращения"),
        types.KeyboardButton(text="👥 Пользователи"),
        types.KeyboardButton(text="⚙️ Настройки")
    ]
    keyboard.add(*buttons)
    return keyboard
