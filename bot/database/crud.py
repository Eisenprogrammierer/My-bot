from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from .models import User, Ticket, AdminLog
from .connector import SessionLocal

class CRUD:
    """
    Класс для операций с базой данных
    """
    
    
    @staticmethod
    def get_user(db: Session, chat_id: int) -> Optional[User]:
        return db.query(User).filter(User.chat_id == chat_id).first()
    

    @staticmethod
    def create_user(db: Session, chat_id: int, username: Optional[str] = None, 
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        db_user = User(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    

    @staticmethod
    def update_user(db: Session, chat_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        user = db.query(User).filter(User.chat_id == chat_id).first()
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user
    

    @staticmethod
    def ban_user(db: Session, chat_id: int) -> Optional[User]:
        return CRUD.update_user(db, chat_id, {"is_banned": True})
    

    @staticmethod
    def unban_user(db: Session, chat_id: int) -> Optional[User]:
        return CRUD.update_user(db, chat_id, {"is_banned": False})
    
    
    @staticmethod
    def create_ticket(db: Session, user_id: int, message: str) -> Ticket:
        db_ticket = Ticket(
            user_id=user_id,
            message=message,
            status="open"
        )
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
        return db_ticket


    @staticmethod
    def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()
    

    @staticmethod
    def get_user_tickets(db: Session, user_id: int, status: Optional[str] = None) -> List[Ticket]:
        query = db.query(Ticket).filter(Ticket.user_id == user_id)
        if status:
            query = query.filter(Ticket.status == status)
        return query.order_by(Ticket.created_at.desc()).all()
    

    @staticmethod
    def get_open_tickets(db: Session) -> List[Ticket]:
        return db.query(Ticket).filter(Ticket.status == "open").order_by(Ticket.created_at).all()
    

    @staticmethod
    def update_ticket(db: Session, ticket_id: int, update_data: Dict[str, Any]) -> Optional[Ticket]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            for key, value in update_data.items():
                setattr(ticket, key, value)
            db.commit()
            db.refresh(ticket)
        return ticket
    

    @staticmethod
    def close_ticket(db: Session, ticket_id: int, admin_id: Optional[int] = None) -> Optional[Ticket]:
        update_data = {"status": "closed"}
        if admin_id:
            update_data["admin_id"] = admin_id
        return CRUD.update_ticket(db, ticket_id, update_data)


    @staticmethod
    def add_response_to_ticket(db: Session, ticket_id: int, response: str, admin_id: Optional[int] = None) -> Optional[Ticket]:
        update_data = {"response": response, "status": "closed"}
        if admin_id:
            update_data["admin_id"] = admin_id
        return CRUD.update_ticket(db, ticket_id, update_data)
    
    
    @staticmethod
    def log_admin_action(db: Session, admin_id: int, action: str, 
                        target_user_id: int, details: Optional[str] = None) -> AdminLog:
        db_log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            details=details
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log


    @staticmethod
    def get_admin_logs(db: Session, admin_id: Optional[int] = None, 
                      limit: int = 100) -> List[AdminLog]:

        query = db.query(AdminLog)
        if admin_id:
            query = query.filter(AdminLog.admin_id == admin_id)
        return query.order_by(AdminLog.created_at.desc()).limit(limit).all()


crud = CRUD()
