from core.database.connection import db_manager
from modules.care_module.models.entities import TestCategory
from core.shared.utils.logger import logger
from datetime import datetime

class TestCategoryService:
    def __init__(self):
        self.logger_name = "TestCategoryService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                category = TestCategory(**data)
                session.add(category)
                session.flush()
                category_id = category.id
                logger.info(f"Test category created: {category.name}", self.logger_name)
                session.expunge(category)
                category.id = category_id
                return category
        except Exception as e:
            logger.error(f"Error creating test category: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestCategory).filter(TestCategory.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestCategory.tenant_id == tenant_id)
                categories = query.all()
                for category in categories:
                    session.expunge(category)
                return categories
        except Exception as e:
            logger.error(f"Error fetching test categories: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, category_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestCategory).filter(
                    TestCategory.id == category_id,
                    TestCategory.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestCategory.tenant_id == tenant_id)
                category = query.first()
                if category:
                    session.expunge(category)
                return category
        except Exception as e:
            logger.error(f"Error fetching test category: {str(e)}", self.logger_name)
            return None
    
    def update(self, category_id, data):
        try:
            with db_manager.get_session() as session:
                category = session.query(TestCategory).filter(
                    TestCategory.id == category_id,
                    TestCategory.is_deleted == False
                ).first()
                if category:
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(category, key, value)
                    category.updated_at = datetime.utcnow()
                    session.flush()
                    logger.info(f"Test category updated: {category.name}", self.logger_name)
                    session.expunge(category)
                    return category
                return None
        except Exception as e:
            logger.error(f"Error updating test category: {str(e)}", self.logger_name)
            raise
    
    def delete(self, category_id):
        try:
            with db_manager.get_session() as session:
                category = session.query(TestCategory).filter(TestCategory.id == category_id).first()
                if category:
                    category.is_deleted = True
                    category.updated_at = datetime.utcnow()
                    logger.info(f"Test category deleted: {category.name}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting test category: {str(e)}", self.logger_name)
            raise
