from core.database.connection import db_manager
from modules.health_module.models.care_entities import Test, TestParameter
from core.shared.utils.logger import logger
from datetime import datetime

class TestService:
    def __init__(self):
        self.logger_name = "TestService"
    
    def create(self, data):
        try:
            # Validate commission_type
            commission_type = data.get('commission_type')
            if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
                raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
            
            with db_manager.get_session() as session:
                parameters = data.pop('parameters', [])
                test = Test(**data)
                session.add(test)
                session.flush()
                
                for param in parameters:
                    param['test_id'] = test.id
                    param['tenant_id'] = data['tenant_id']
                    test_param = TestParameter(**param)
                    session.add(test_param)
                
                test_id = test.id
                logger.info(f"Test created: {test.name}", self.logger_name)
                session.expunge(test)
                test.id = test_id
                return test
        except Exception as e:
            logger.error(f"Error creating test: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Test).filter(Test.is_deleted == False)
                if tenant_id:
                    query = query.filter(Test.tenant_id == tenant_id)
                tests = query.all()
                for test in tests:
                    session.expunge(test)
                return tests
        except Exception as e:
            logger.error(f"Error fetching tests: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, test_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Test).filter(Test.id == test_id, Test.is_deleted == False)
                if tenant_id:
                    query = query.filter(Test.tenant_id == tenant_id)
                test = query.first()
                if test:
                    session.expunge(test)
                return test
        except Exception as e:
            logger.error(f"Error fetching test: {str(e)}", self.logger_name)
            return None
    
    def update(self, test_id, data):
        try:
            # Validate commission_type
            commission_type = data.get('commission_type')
            if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
                raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
            
            with db_manager.get_session() as session:
                test = session.query(Test).filter(Test.id == test_id, Test.is_deleted == False).first()
                if test:
                    parameters = data.pop('parameters', None)
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(test, key, value)
                    test.updated_at = datetime.utcnow()
                    
                    if parameters is not None:
                        session.query(TestParameter).filter(TestParameter.test_id == test_id).update({'is_deleted': True})
                        session.flush()
                        for param in parameters:
                            param.pop('id', None)
                            param['test_id'] = test_id
                            param['tenant_id'] = test.tenant_id
                            test_param = TestParameter(**param)
                            session.add(test_param)
                    
                    session.flush()
                    logger.info(f"Test updated: {test.name}", self.logger_name)
                    session.expunge(test)
                    return test
                return None
        except Exception as e:
            logger.error(f"Error updating test: {str(e)}", self.logger_name)
            raise
    
    def delete(self, test_id):
        try:
            with db_manager.get_session() as session:
                test = session.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.is_deleted = True
                    test.updated_at = datetime.utcnow()
                    session.query(TestParameter).filter(TestParameter.test_id == test_id).update({'is_deleted': True})
                    logger.info(f"Test deleted: {test.name}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting test: {str(e)}", self.logger_name)
            raise
    
    def get_parameters(self, test_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestParameter).filter(
                    TestParameter.test_id == test_id,
                    TestParameter.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestParameter.tenant_id == tenant_id)
                params = query.all()
                for param in params:
                    session.expunge(param)
                return params
        except Exception as e:
            logger.error(f"Error fetching test parameters: {str(e)}", self.logger_name)
            return []
