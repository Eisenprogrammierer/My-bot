import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from typing import Generator
from bot.config import Config


logger = logging.getLogger(__name__)


Base = declarative_base()


class DatabaseConnector:
    """
    Класс для управления подключениями к базе данных.
    
    Обеспечивает:
    - Инициализацию подключения
    - Управление сессиями
    - Автоматическое закрытие соединений
    """
    

    def __init__(self, db_url: str = None, echo: bool = False):
        """
        Инициализация подключения к БД.
        
        :param db_url: URL подключения к БД (например, 'sqlite:///database.db')
        :param echo: Логировать SQL-запросы (для отладки)
        """
        self.db_url = db_url or Config.DB_URL
        self.engine = None
        self.session_factory = None
        self.echo = echo
        self.initialize()


    def initialize(self):
        try:
            self.engine = create_engine(
                self.db_url,
                echo=self.echo,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600
            )
            self.session_factory = scoped_session(
                sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False
                )
            )
            logger.info(f"Database connection initialized for {self.db_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise


    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise


    @contextmanager
    def session_scope(self) -> Generator:
        """
        Контекстный менеджер для работы с сессией БД.
        
        Обеспечивает:
        - Автоматическое создание сессии
        - Коммит при успешном завершении
        - Откат при исключении
        - Закрытие сессии в любом случае
        
        Пример использования:
        with db.session_scope() as session:
            session.add(some_object)
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
            logger.debug("Session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Session rolled back due to error: {str(e)}")
            raise
        finally:
            session.close()
            logger.debug("Session closed")


    def close(self):
        if self.session_factory:
            self.session_factory.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")


db_connector = DatabaseConnector()

def init_db(db_url: str = None, create_tables: bool = True) -> DatabaseConnector:
    """
    Инициализация базы данных.
    
    :param db_url: URL подключения к БД (если None, берется из конфига)
    :param create_tables: Создавать таблицы при инициализации
    :return: Экземпляр DatabaseConnector
    """
    global db_connector
    db_connector = DatabaseConnector(db_url)
    if create_tables:
        db_connector.create_tables()
    return db_connector

def get_db_session():
    return db_connector.session_factory()


SessionLocal = db_connector.session_factory
