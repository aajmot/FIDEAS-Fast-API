from modules.admin_module.models.entities import Tenant
from modules.admin_module.services.base_service import BaseService

class TenantService(BaseService):
    def __init__(self):
        super().__init__(Tenant)