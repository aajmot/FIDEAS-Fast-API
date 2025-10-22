class SessionManager:
    _instance = None
    _session_data = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_session_data(cls, data):
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._session_data = data
    
    @classmethod
    def get_session_data(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance._session_data
    
    @classmethod
    def clear_session(cls):
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._session_data = {}
    
    def set_current_user(self, user):
        self._session_data['user'] = user
        if isinstance(user, dict) and 'tenant_id' in user:
            self._session_data['tenant_id'] = user['tenant_id']
        elif hasattr(user, 'tenant_id'):
            self._session_data['tenant_id'] = user.tenant_id
    
    def get_current_user(self):
        return self._session_data.get('user')
    
    def get_current_tenant_id(self):
        return self._session_data.get('tenant_id')
    
    def get_current_username(self):
        return self._session_data.get('username')
    
    def get_current_user_id(self):
        return self._session_data.get('user_id')
    
    def get_current_tenant_name(self):
        return self._session_data.get('tenant_name')

# Global session manager instance
session_manager = SessionManager()