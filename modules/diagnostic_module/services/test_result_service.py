from core.database.connection import db_manager
from modules.diagnostic_module.models.entities import TestResult, TestResultDetail, TestResultFile
from core.shared.utils.logger import logger
from datetime import datetime

class TestResultService:
    def __init__(self):
        self.logger_name = "TestResultService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                details = data.pop('details', [])
                files = data.pop('files', [])
                result = TestResult(**data)
                session.add(result)
                session.flush()
                
                for detail in details:
                    detail['test_result_id'] = result.id
                    detail['tenant_id'] = data['tenant_id']
                    result_detail = TestResultDetail(**detail)
                    session.add(result_detail)
                
                for file in files:
                    file['test_result_id'] = result.id
                    file['tenant_id'] = data['tenant_id']
                    result_file = TestResultFile(**file)
                    session.add(result_file)
                
                result_id = result.id
                logger.info(f"Test result created: {result_id}", self.logger_name)
                session.expunge(result)
                result.id = result_id
                return result
        except Exception as e:
            logger.error(f"Error creating test result: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestResult).filter(TestResult.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestResult.tenant_id == tenant_id)
                results = query.all()
                for result in results:
                    session.expunge(result)
                return results
        except Exception as e:
            logger.error(f"Error fetching test results: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, result_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestResult).filter(TestResult.id == result_id, TestResult.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestResult.tenant_id == tenant_id)
                result = query.first()
                if result:
                    session.expunge(result)
                return result
        except Exception as e:
            logger.error(f"Error fetching test result: {str(e)}", self.logger_name)
            return None
    
    def update(self, result_id, data):
        try:
            with db_manager.get_session() as session:
                result = session.query(TestResult).filter(TestResult.id == result_id, TestResult.is_deleted == False).first()
                if result:
                    details = data.pop('details', None)
                    files = data.pop('files', None)
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(result, key, value)
                    result.updated_at = datetime.utcnow()
                    
                    if details is not None:
                        session.query(TestResultDetail).filter(TestResultDetail.test_result_id == result_id).update({'is_deleted': True})
                        session.flush()
                        for detail in details:
                            detail.pop('id', None)
                            detail['test_result_id'] = result_id
                            detail['tenant_id'] = result.tenant_id
                            result_detail = TestResultDetail(**detail)
                            session.add(result_detail)
                    
                    if files is not None:
                        session.query(TestResultFile).filter(TestResultFile.test_result_id == result_id).update({'is_deleted': True})
                        session.flush()
                        for file in files:
                            file.pop('id', None)
                            file['test_result_id'] = result_id
                            file['tenant_id'] = result.tenant_id
                            result_file = TestResultFile(**file)
                            session.add(result_file)
                    
                    session.flush()
                    logger.info(f"Test result updated: {result_id}", self.logger_name)
                    session.expunge(result)
                    return result
                return None
        except Exception as e:
            logger.error(f"Error updating test result: {str(e)}", self.logger_name)
            raise
    
    def delete(self, result_id):
        try:
            with db_manager.get_session() as session:
                result = session.query(TestResult).filter(TestResult.id == result_id).first()
                if result:
                    result.is_deleted = True
                    result.updated_at = datetime.utcnow()
                    session.query(TestResultDetail).filter(TestResultDetail.test_result_id == result_id).update({'is_deleted': True})
                    session.query(TestResultFile).filter(TestResultFile.test_result_id == result_id).update({'is_deleted': True})
                    logger.info(f"Test result deleted: {result_id}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting test result: {str(e)}", self.logger_name)
            raise
    
    def get_details(self, result_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestResultDetail).filter(
                    TestResultDetail.test_result_id == result_id,
                    TestResultDetail.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestResultDetail.tenant_id == tenant_id)
                details = query.all()
                for detail in details:
                    session.expunge(detail)
                return details
        except Exception as e:
            logger.error(f"Error fetching test result details: {str(e)}", self.logger_name)
            return []
    
    def get_files(self, result_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestResultFile).filter(
                    TestResultFile.test_result_id == result_id,
                    TestResultFile.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestResultFile.tenant_id == tenant_id)
                files = query.all()
                for file in files:
                    session.expunge(file)
                return files
        except Exception as e:
            logger.error(f"Error fetching test result files: {str(e)}", self.logger_name)
            return []
    
    def get_by_order_id(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestResult).filter(
                    TestResult.test_order_id == order_id,
                    TestResult.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestResult.tenant_id == tenant_id)
                results = query.all()
                for result in results:
                    session.expunge(result)
                return results
        except Exception as e:
            logger.error(f"Error fetching test results by order: {str(e)}", self.logger_name)
            return []
