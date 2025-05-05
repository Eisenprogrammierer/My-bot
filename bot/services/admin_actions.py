import logging

from typing import Optional, Dict, List
from telebot import TeleBot, types
from bot.database import crud
from bot.database.connector import db_connector
from bot.config import Config, BotMessages
from bot.services.messaging import MessagingService
from bot.utils.keyboards import get_admin_main_keyboard


logger = logging.getLogger(__name__)


class AdminActions:

    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.messaging = MessagingService(bot)


    def ban_user(
        self,
        admin_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> bool:
        with db_connector.session_scope() as session:
            if admin_id not in Config.ADMIN_IDS:
                logger.warning(f"Unauthorized ban attempt by {admin_id}")
                return False

            user = crud.get_user(session, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            if user.is_banned:
                logger.info(f"User {user_id} already banned")
                return True

            crud.update_user(session, user.id, {"is_banned": True})

            crud.log_admin_action(
                session,
                admin_id=admin_id,
                action="ban",
                target_user_id=user.id,
                details=reason or "No reason provided"
            )

            try:
                self.messaging.send_message(
                    user.chat_id,
                    BotMessages.BAN_NOTIFICATION.format(reason=reason or "нарушение правил")
                )
            except Exception as e:
                logger.error(f"Failed to notify user about ban: {e}")

            open_tickets = crud.get_user_tickets(session, user.id, status="open")
            for ticket in open_tickets:
                crud.update_ticket(
                    session,
                    ticket.id,
                    {"status": "closed", "admin_id": admin_id}
                )

            logger.info(f"User {user_id} banned by admin {admin_id}")
            return True


    def unban_user(self, admin_id: int, user_id: int) -> bool:
        with db_connector.session_scope() as session:
            if admin_id not in Config.ADMIN_IDS:
                logger.warning(f"Unauthorized unban attempt by {admin_id}")
                return False

            user = crud.get_user(session, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            if not user.is_banned:
                logger.info(f"User {user_id} not banned")
                return True

            crud.update_user(session, user.id, {"is_banned": False})

            crud.log_admin_action(
                session,
                admin_id=admin_id,
                action="unban",
                target_user_id=user.id,
                details="User unbanned"
            )


            try:
                self.messaging.send_message(
                    user.chat_id,
                    BotMessages.UNBAN_NOTIFICATION
                )
            except Exception as e:
                logger.error(f"Failed to notify user about unban: {e}")

            logger.info(f"User {user_id} unbanned by admin {admin_id}")
            return True


    def close_ticket(
        self,
        admin_id: int,
        ticket_id: int,
        comment: Optional[str] = None
    ) -> bool:
        with db_connector.session_scope() as session:
            ticket = crud.get_ticket(session, ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return False

            if ticket.status == "closed":
                logger.info(f"Ticket {ticket_id} already closed")
                return True

            update_data = {
                "status": "closed",
                "admin_id": admin_id
            }
            if comment:
                update_data["response"] = comment

            crud.update_ticket(session, ticket.id, update_data)

            crud.log_admin_action(
                session,
                admin_id=admin_id,
                action="close_ticket",
                target_user_id=ticket.user_id,
                details=f"Ticket #{ticket_id}"
            )

            logger.info(f"Ticket {ticket_id} closed by admin {admin_id}")
            return True


    def get_user_stats(self, user_id: int) -> Optional[Dict[str, int]]:
        with db_connector.session_scope() as session:
            user = crud.get_user(session, user_id)
            if not user:
                return None

            all_tickets = crud.get_user_tickets(session, user.id)
            open_tickets = crud.get_user_tickets(session, user.id, status="open")

            return {
                "total_tickets": len(all_tickets),
                "open_tickets": len(open_tickets),
                "closed_tickets": len(all_tickets) - len(open_tickets)
            }


    def get_system_stats(self) -> Dict[str, int]:
        with db_connector.session_scope() as session:
            total_users = session.query(crud.User).count()
            banned_users = session.query(crud.User).filter(crud.User.is_banned == True).count()
            total_tickets = session.query(crud.Ticket).count()
            open_tickets = session.query(crud.Ticket).filter(crud.Ticket.status == "open").count()

            return {
                "total_users": total_users,
                "banned_users": banned_users,
                "total_tickets": total_tickets,
                "open_tickets": open_tickets
            }


    def show_admin_panel(self, admin_id: int):
        stats = self.get_system_stats()
        stats_message = (
            "📊 <b>Статистика системы</b>\n\n"
            f"👥 Пользователей: {stats['total_users']}\n"
            f"⛔ Заблокировано: {stats['banned_users']}\n"
            f"📨 Обращений: {stats['total_tickets']}\n"
            f"✓ Открытых: {stats['open_tickets']}"
        )

        self.messaging.send_message(
            admin_id,
            stats_message,
            reply_markup=get_admin_main_keyboard()
        )
