from core.database.connection import db_manager
from modules.diagnostic_module.models.entities import TestPanel, TestPanelItem
from core.shared.utils.logger import logger
from datetime import datetime

class TestPanelService:
    def __init__(self):
        self.logger_name = "TestPanelService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                panel = TestPanel(**data)
                session.add(panel)
                session.flush()
                
                for item in items:
                    item['panel_id'] = panel.id
                    item['tenant_id'] = data['tenant_id']
                    panel_item = TestPanelItem(**item)
                    session.add(panel_item)
                
                panel_id = panel.id
                logger.info(f"Test panel created: {panel.name}", self.logger_name)
                session.expunge(panel)
                panel.id = panel_id
                return panel
        except Exception as e:
            logger.error(f"Error creating test panel: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestPanel).filter(TestPanel.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestPanel.tenant_id == tenant_id)
                panels = query.all()
                for panel in panels:
                    session.expunge(panel)
                return panels
        except Exception as e:
            logger.error(f"Error fetching test panels: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, panel_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestPanel).filter(TestPanel.id == panel_id, TestPanel.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestPanel.tenant_id == tenant_id)
                panel = query.first()
                if panel:
                    session.expunge(panel)
                return panel
        except Exception as e:
            logger.error(f"Error fetching test panel: {str(e)}", self.logger_name)
            return None
    
    def update(self, panel_id, data):
        try:
            with db_manager.get_session() as session:
                panel = session.query(TestPanel).filter(TestPanel.id == panel_id, TestPanel.is_deleted == False).first()
                if panel:
                    items = data.pop('items', None)
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(panel, key, value)
                    panel.updated_at = datetime.utcnow()
                    
                    if items is not None:
                        session.query(TestPanelItem).filter(TestPanelItem.panel_id == panel_id).update({'is_deleted': True})
                        session.flush()
                        for item in items:
                            item.pop('id', None)
                            item['panel_id'] = panel_id
                            item['tenant_id'] = panel.tenant_id
                            panel_item = TestPanelItem(**item)
                            session.add(panel_item)
                    
                    session.flush()
                    logger.info(f"Test panel updated: {panel.name}", self.logger_name)
                    session.expunge(panel)
                    return panel
                return None
        except Exception as e:
            logger.error(f"Error updating test panel: {str(e)}", self.logger_name)
            raise
    
    def delete(self, panel_id):
        try:
            with db_manager.get_session() as session:
                panel = session.query(TestPanel).filter(TestPanel.id == panel_id).first()
                if panel:
                    panel.is_deleted = True
                    panel.updated_at = datetime.utcnow()
                    session.query(TestPanelItem).filter(TestPanelItem.panel_id == panel_id).update({'is_deleted': True})
                    logger.info(f"Test panel deleted: {panel.name}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting test panel: {str(e)}", self.logger_name)
            raise
    
    def get_items(self, panel_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestPanelItem).filter(
                    TestPanelItem.panel_id == panel_id,
                    TestPanelItem.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestPanelItem.tenant_id == tenant_id)
                items = query.all()
                for item in items:
                    session.expunge(item)
                return items
        except Exception as e:
            logger.error(f"Error fetching test panel items: {str(e)}", self.logger_name)
            return []
