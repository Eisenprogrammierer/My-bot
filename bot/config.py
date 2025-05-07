import os
from dotenv import load_dotenv
from typing import Dict, Any


load_dotenv()


class Laguages:
    EN = "en"
    DE = "de"
    RU = "ru"


DEFAULT_LANGUAGE = Languages.EN


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DB_URL = os.getenv("DB_URL", "sqlite:///tickets.db")
    ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_]


class BotMessages:
    WELCOME_MESSAGE = {
            Languages.RU : "👋 Добро пожаловать в службу поддержки!\n\n\
        📨 Отправьте ваше сообщение, и администратор ответит вам \
        в ближайшее время.\n\n\
        🛠 Доступные команды:\n\
        /help - показать это сообщение\n\
        /mytickets - мои обращения",
            Languages.EN : "👋 Welcome to customer service!\n\n\
        📨 Send your message and an administrator will get back to you\
        as soon as possible. \n\n\
        🛠 Available commands:\n\
        /help - show this message\n\
        /mytickets - my tickets",
            Languages.DE : "👋 Willkommen in unserem Support-Team!\n\n\
        📨 Senden Sie Ihre Nachricht, und ein Administrator wird sich mit Ihnen in Verbindung setzen\
        so schnell wie möglich zurückmelden.\n\n\
        🛠 Verfügbare Befehle:\n\
        /help - diese Nachricht anzeigen.\n\
        /mytickets - meine Appelle"
        }

    BANNED_MESSAGE = {
            Languages.RU : "⛔ Ваш аккаунт заблокирован администратором",
            Languages.EN : "⛔ Your account has been blocked by an administrator",
            Languages.DE : "⛔ Ihr Konto wurde von einem Administrator gesperrt"
            }

    ACCESS_DENIED = {
            Language.RU : "⛔ Доступ запрещен",
            Language.EN : "⛔ Access denied",
            Language.DE : "⛔ Zugriff verweigert"
            }

    NO_TICKETS = {
            Language.RU : "📭 У вас пока нет обращений",
            Language.EN : "📭 You have no tickets yet",
            Language.DE : "📭 Sie haben noch keine Appelle"
            }

    TICKETS_HEADER = {
            Language.RU : "📂 Ваши обращения:",
            Language.EN : "📂 Your tickets:",
            Language.DE : "📂 Ihre Appelle:"
            }

    TICKET_ITEM = (
        "{status_icon} #{ticket_id} - {status}\n"
        "📅 {date}\n"
        "📝 {preview}..."
    )

    TICKET_CREATED = {
            Language.RU : "✅ Ваше обращение принято под номером #{ticket_id}\n\
        Администратор ответит вам в ближайшее время.",
            Language.EN : "✅ Your ticket has been accepted under #{ticket_id}\n\
        The administrator will reply to you as soon as possible.",
            Language.DE : "✅ Ihre Appelle wurde unter #{ticket_id} angenommen\n\
        Der Administrator wird Ihnen so bald wie möglich antworten."
            }

    ADMIN_NOTIFICATION = {
            Language.RU : "📩 Новое обращение #{ticket_id}\n\
        👤 Пользователь: @{username} (ID: {user_id})\n\
        📅 Дата: {date}\n\n\
        📝 Текст:\n{message}",
            Language.EN : "📩 New ticket #{ticket_id}\n\
        👤 User: @{username} (ID: {user_id})\n\
        📅 Date: {date}\n\n\
        📝 Text:\n{message}",
            Language.DE : "📩 Neue Appelle #{ticket_id}\n\
        👤 Benutzer: @{username} (ID: {user_id})\n\
        📅 Datum: {date}\n\n\
        📝 Text:\n{message}"
            }

    LANGUAGE_SELECT = {
            Languages.RU: "🌐 Выберите язык:",
            Languages.EN: "🌐 Please select language:",
            Languages.DE: "🌐 Bitte wählen Sie die Sprache:"
            }
