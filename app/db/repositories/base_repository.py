from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.base_model import Base
from app.core.exceptions.custom_exceptions import DatabaseException

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to get {self.model.__name__}: {str(e)}")
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to get {self.model.__name__} list: {str(e)}")
    
    def create(self, obj_in: dict) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """Update an existing record"""
        try:
            db_obj = self.get(id)
            if db_obj:
                for field, value in obj_in.items():
                    setattr(db_obj, field, value)
                self.db.commit()
                self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to update {self.model.__name__}: {str(e)}")
    
    def delete(self, id: int) -> bool:
        """Delete a record"""
        try:
            db_obj = self.get(id)
            if db_obj:
                self.db.delete(db_obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def count(self) -> int:
        """Count total records"""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to count {self.model.__name__}: {str(e)}")