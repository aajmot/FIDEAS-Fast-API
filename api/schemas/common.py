from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from fastapi import Query

class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    success: bool
    message: str
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(100, ge=1, le=1000, description="Items per page"),
        search: Optional[str] = Query(None, description="Search term")
    ):
        self.page = page
        self.per_page = per_page
        self.search = search
        self.offset = (page - 1) * per_page

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class CreateRequest(BaseModel):
    pass

class UpdateRequest(BaseModel):
    pass