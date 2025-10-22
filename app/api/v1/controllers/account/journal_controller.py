from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.core.utils.api_response import BaseResponse, PaginatedResponse
from app.core.utils.pagination import PaginationParams
from app.modules.account.services.journal_service import JournalService

router = APIRouter()

@router.get("/journal-entries", response_model=PaginatedResponse)
async def get_journal_entries(pagination: PaginationParams = Depends()):
    try:
        service = JournalService()
        journals = service.get_all()
        return PaginatedResponse(
            success=True,
            message="Journal entries retrieved successfully",
            data=[journal.__dict__ for journal in journals],
            total=len(journals),
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=1
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/journal-entries", response_model=BaseResponse)
async def create_journal_entry(journal_data: Dict[str, Any]):
    try:
        service = JournalService()
        journal = service.create(journal_data)
        return BaseResponse(
            success=True,
            message="Journal entry created successfully",
            data={"id": journal.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/journal-entries/{journal_id}", response_model=BaseResponse)
async def get_journal_entry(journal_id: int):
    try:
        service = JournalService()
        journal = service.get_by_id(journal_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return BaseResponse(
            success=True,
            message="Journal entry retrieved successfully",
            data=journal.__dict__
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/journal-entries/{journal_id}", response_model=BaseResponse)
async def update_journal_entry(journal_id: int, journal_data: Dict[str, Any]):
    try:
        service = JournalService()
        journal = service.update(journal_id, journal_data)
        return BaseResponse(
            success=True,
            message="Journal entry updated successfully",
            data={"id": journal.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/journal-entries/{journal_id}", response_model=BaseResponse)
async def delete_journal_entry(journal_id: int):
    try:
        service = JournalService()
        service.delete(journal_id)
        return BaseResponse(
            success=True,
            message="Journal entry deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))