import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DB_URL = os.getenv("DB_URL", "sqlite:///tickets.db")
    ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_]


class BotMessages:
    WELCOME_MESSAGE = (
        "👋 Добро пожаловать в службу поддержки!\n\n"
        "📨 Отправьте ваше сообщение, и администратор ответит вам "
        "в ближайшее время.\n\n"
        "🛠 Доступные команды:\n"
        "/help - показать это сообщение\n"
        "/mytickets - мои обращения"
    )


    BANNED_MESSAGE = "⛔ Ваш аккаунт заблокирован администратором"
    ACCESS_DENIED = "⛔ Доступ запрещен"


    NO_TICKETS = "📭 У вас пока нет обращений"
    TICKETS_HEADER = "📂 Ваши обращения:"
    TICKET_ITEM = (
        "{status_icon} #{ticket_id} - {status}\n"
        "📅 {date}\n"
        "📝 {preview}..."
    )
    TICKET_CREATED = (
        "✅ Ваше обращение принято под номером #{ticket_id}\n"
        "Администратор ответит вам в ближайшее время."
    )


    ADMIN_NOTIFICATION = (
        "📩 Новое обращение #{ticket_id}\n"
        "👤 Пользователь: @{username} (ID: {user_id})\n"
        "📅 Дата: {date}\n\n"
        "📝 Текст:\n{message}"
    )
