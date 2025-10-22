from typing import Generic, TypeVar, List, Optional, Tuple
from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 10
    search: Optional[str] = None
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        size: int
    ):
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


def paginate_query(
    query,
    pagination: PaginationParams
) -> Tuple[List, int]:
    """Paginate SQLAlchemy query"""
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.size).all()
    return items, total