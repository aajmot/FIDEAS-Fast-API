# Re-export admin route submodules
from . import users_route
from . import menus_route
from . import roles_route
from . import tenant_route
from . import legal_entities_route
from . import financial_years_route
from . import agencies_route
from . import role_menu_mappings_route
from . import transaction_templates_route
from . import account_configurations_route
from . import accounts_route
from . import branches_route

__all__ = [
    "users_route",
    "menus_route",
    "roles_route",
    "tenant_route",
    "legal_entities_route",
    "financial_years_route",
    "agencies_route",
    "role_menu_mappings_route",
    "transaction_templates_route",
    "account_configurations_route",
    "accounts_route",
    "branches_route",
]
# API v1 routers
