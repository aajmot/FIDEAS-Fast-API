from pydantic import BaseModel
from typing import Optional

class UpdateUserInfoRequest(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
