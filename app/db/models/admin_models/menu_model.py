from sqlalchemy import Column, Integer, String, Boolean
from app.db.models.base_model import BaseModel

class MenuMaster(BaseModel):
    __tablename__ = 'menu_master'
    
    menu_name = Column(String(100), nullable=False)
    menu_code = Column(String(50), nullable=False, unique=True)
    module_code = Column(String(50), nullable=False)
    parent_menu_id = Column(Integer)
    icon = Column(String(100))
    route = Column(String(200))
    sort_order = Column(Integer, default=0)
    is_admin_only = Column(Boolean, default=False)

class RoleMenuMapping(BaseModel):
    __tablename__ = 'role_menu_mapping'
    
    role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    can_create = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_import = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)
    can_print = Column(Boolean, default=False)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))