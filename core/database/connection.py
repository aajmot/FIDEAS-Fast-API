import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from core.shared.utils.logger import logger
from core.shared.middleware.exception_handler import ExceptionMiddleware

Base = declarative_base()

class DatabaseManager:
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._initialize_database()
    
    @ExceptionMiddleware.handle_exceptions("DatabaseManager")
    def _initialize_database(self):
        database_url = os.getenv('DATABASE_URL')
        pool_size = int(os.getenv('DB_POOL_SIZE', 10))
        max_overflow = int(os.getenv('DB_MAX_OVERFLOW', 20))
        
        self._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            echo=False
        )
        
        # Keep ORM instances usable after commit to avoid DetachedInstanceError
        # (expire_on_commit=False prevents SQLAlchemy from expiring attributes
        # when the session commits and closes)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        logger.info("Database connection pool initialized", "DatabaseManager")
    
    @contextmanager
    def get_session(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}", "DatabaseManager")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        Base.metadata.create_all(self._engine)
        logger.info("Database tables created", "DatabaseManager")

db_manager = DatabaseManager()