import os
from dotenv import load_dotenv
from typing import Dict, Any


load_dotenv()


class Languages:
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
            Languages.EN : "👋 Welcome to support service!\n\n\
        📨 Send your message and an administrator will get back to you\
        as soon as possible. \n\n\
        🛠 Available commands:\n\
        /help - show this message\n\
        /mytickets - my tickets",
            Languages.DE : "👋 Willkommen in unserem Support-Team!\n\n\
        📨 Senden Sie Ihre Nachricht, und ein Administrator wird sich mit Ihnen in Verbindung setzen\
        so schnell wie möglich antworten.\n\n\
        🛠 Verfügbare Befehle:\n\
        /help - diese Nachricht anzeigen.\n\
        /mytickets - meine Anfragen"
        }

    BANNED_MESSAGE = {
            Languages.RU : "⛔ Ваш аккаунт заблокирован администратором",
            Languages.EN : "⛔ Your account has been blocked by an administrator",
            Languages.DE : "⛔ Ihr Konto wurde von einem Administrator gesperrt"
            }

    ACCESS_DENIED = {
            Languages.RU : "⛔ Доступ запрещен",
            Languages.EN : "⛔ Access denied",
            Languages.DE : "⛔ Zugriff verweigert"
            }

    NO_TICKETS = {
            Languages.RU : "📭 У вас пока нет обращений",
            Languages.EN : "📭 You have no tickets yet",
            Languages.DE : "📭 Sie haben noch keine Anfragen"
            }

    TICKETS_HEADER = {
            Languages.RU : "📂 Ваши обращения:",
            Languages.EN : "📂 Your tickets:",
            Languages.DE : "📂 Ihre Anfragen:"
            }

    TICKET_ITEM = (
        "{status_icon} #{ticket_id} - {status}\n"
        "📅 {date}\n"
        "📝 {preview}..."
    )

    TICKET_CREATED = {
            Languages.RU : "✅ Ваше обращение принято под номером #{ticket_id}\n\
        Администратор ответит вам в ближайшее время.",
            Languages.EN : "✅ Your ticket #{ticket_id} has been created\n\
        The administrator will reply to you as soon as possible.",
            Languages.DE : "✅ Ihr Anfrag wurde unter #{ticket_id} angenommen\n\
        Der Administrator wird Ihnen so bald wie möglich antworten."
            }

    ADMIN_NOTIFICATION = {
            Languages.RU : "📩 Новое обращение #{ticket_id}\n\
        👤 Пользователь: @{username} (ID: {user_id})\n\
        📅 Дата: {date}\n\n\
        📝 Текст:\n{message}",
            Languages.EN : "📩 New ticket #{ticket_id}\n\
        👤 User: @{username} (ID: {user_id})\n\
        📅 Date: {date}\n\n\
        📝 Text:\n{message}",
            Languages.DE : "📩 Neu Anfrag #{ticket_id}\n\
        👤 Benutzer: @{username} (ID: {user_id})\n\
        📅 Datum: {date}\n\n\
        📝 Text:\n{message}"
            }

    LANGUAGE_SELECT = {
            Languages.RU: "🌐 Выберите язык:",
            Languages.EN: "🌐 Please select language:",
            Languages.DE: "🌐 Bitte wählen Sie die Sprache:"
            }
