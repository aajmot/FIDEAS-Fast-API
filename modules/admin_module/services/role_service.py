from modules.admin_module.models.entities import Role
from modules.admin_module.services.base_service import BaseService

class RoleService(BaseService):
    def __init__(self):
        super().__init__(Role)