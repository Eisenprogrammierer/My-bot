from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from bot.config import Config


Base = declarative_base()


class User(Base):
    """
    Модель пользователя Telegram
    
    Атрибуты:
        id (int): Первичный ключ
        chat_id (int): Уникальный идентификатор чата с пользователем
        username (str): Опциональное имя пользователя (@username)
        first_name (str): Имя пользователя
        last_name (str): Фамилия пользователя (опционально)
        is_banned (bool): Флаг блокировки пользователя
        created_at (DateTime): Время создания записи
        updated_at (DateTime): Время последнего обновления
        language (str): Язык пользователя
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    language = Column(String(2), default=Config.DEFAULT_LANGUAGE)

    def __repr__(self):
        return f"<User(id={self.id}, username=@{self.username or 'N/A'})>"


class Ticket(Base):
    """
    Модель обращения пользователя
    
    Атрибуты:
        id (int): Первичный ключ
        user_id (int): Ссылка на пользователя (не ForeignKey для упрощения)
        message (str): Текст обращения
        status (str): Статус ('open', 'closed', 'pending')
        admin_id (int): ID администратора, работающего с обращением (опционально)
        response (str): Текст ответа администратора (опционально)
        created_at (DateTime): Время создания обращения
        updated_at (DateTime): Время последнего обновления
    """
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # Можно сделать ForeignKey в продакшене
    message = Column(Text, nullable=False)
    status = Column(String(20), default='open', nullable=False)
    admin_id = Column(Integer, nullable=True)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Ticket(id={self.id}, status={self.status}, user_id={self.user_id})>"


class AdminLog(Base):
    """
    Модель для логирования действий администраторов
    
    Атрибуты:
        id (int): Первичный ключ
        admin_id (int): ID администратора
        action (str): Тип действия ('ban', 'reply', 'close')
        target_user_id (int): ID целевого пользователя
        details (str): Дополнительная информация
        created_at (DateTime): Время действия
    """
    __tablename__ = 'admin_logs'

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    target_user_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AdminLog(admin={self.admin_id}, action={self.action})>"
