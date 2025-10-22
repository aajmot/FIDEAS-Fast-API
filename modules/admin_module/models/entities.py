from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base
import bcrypt

class Tenant(Base):
    __tablename__ = 'tenants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    description = Column(Text)
    logo = Column(String(255))
    tagline = Column(String(255))
    address = Column(Text)
    business_type = Column(String(20), default='TRADING')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    legal_entities = relationship("LegalEntity", back_populates="tenant")
    users = relationship("User", back_populates="tenant")
    tenant_modules = relationship("TenantModuleMapping", back_populates="tenant")
    settings = relationship("TenantSetting", back_populates="tenant")

class LegalEntity(Base):
    __tablename__ = 'legal_entities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    registration_number = Column(String(50), unique=True)
    address = Column(Text)
    logo = Column(String(255))
    admin_user_id = Column(Integer, ForeignKey('users.id'))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    tenant = relationship("Tenant", back_populates="legal_entities")
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_legal_entity_code_tenant'),
    )

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    user_roles = relationship("UserRole", back_populates="role")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_tenant_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    tenant = relationship("Tenant", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", foreign_keys="UserRole.user_id")
    
    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            # Handle legacy or invalid password hashes
            return False

class UserRole(Base):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey('users.id'))
    created_by = Column(String(100))
    
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])

# FinancialYear moved to account_module as FiscalYear
# Import from there if needed: from modules.account_module.models.entities import FiscalYear

class ModuleMaster(Base):
    __tablename__ = 'module_master'
    
    id = Column(Integer, primary_key=True)
    module_name = Column(String(100), nullable=False, unique=True)
    module_code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant_mappings = relationship("TenantModuleMapping", back_populates="module")

class TenantModuleMapping(Base):
    __tablename__ = 'tenant_module_mapping'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('module_master.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    tenant = relationship("Tenant", back_populates="tenant_modules")
    module = relationship("ModuleMaster", back_populates="tenant_mappings")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'module_id', name='uq_tenant_module_mapping'),
    )

class MenuMaster(Base):
    __tablename__ = 'menu_master'
    
    id = Column(Integer, primary_key=True)
    menu_name = Column(String(100), nullable=False)
    menu_code = Column(String(50), nullable=False, unique=True)
    module_code = Column(String(50), nullable=False)
    parent_menu_id = Column(Integer, ForeignKey('menu_master.id'))
    icon = Column(String(100))
    route = Column(String(200))
    sort_order = Column(Integer, default=0)
    is_admin_only = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("MenuMaster", remote_side=[id], backref="children")
    role_menu_mappings = relationship("RoleMenuMapping", back_populates="menu")

class RoleMenuMapping(Base):
    __tablename__ = 'role_menu_mapping'
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    menu_id = Column(Integer, ForeignKey('menu_master.id'), nullable=False)
    can_create = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_import = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)
    can_print = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    role = relationship("Role")
    menu = relationship("MenuMaster", back_populates="role_menu_mappings")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'menu_id', name='uq_role_menu_mapping'),
    )

class TenantSetting(Base):
    __tablename__ = 'tenant_settings'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    setting = Column(Text, nullable=False)
    description = Column(Text)
    value_type = Column(Text, default='BOOLEAN')
    value = Column(Text, default='TRUE')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    tenant = relationship("Tenant", back_populates="settings")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'setting', name='uq_tenant_setting'),
    )