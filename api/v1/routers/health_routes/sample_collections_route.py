from fastapi import APIRouter, HTTPException, Depends

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.sample_collection_schema import SampleCollectionCreateSchema, SampleCollectionUpdateSchema
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.sample_collection_service import SampleCollectionService

router = APIRouter()

@router.get("/sample-collections", response_model=PaginatedResponse)
async def get_sample_collections(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    service = SampleCollectionService()
    result = service.get_paginated(
        tenant_id=current_user["tenant_id"],
        page=pagination.page,
        per_page=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Sample collections retrieved successfully",
        **result
    )

@router.post("/sample-collections", response_model=BaseResponse)
async def create_sample_collection(collection_data: SampleCollectionCreateSchema, current_user: dict = Depends(get_current_user)):
    service = SampleCollectionService()
    collection_dict = collection_data.dict()
    collection_dict["tenant_id"] = current_user["tenant_id"]
    collection_dict["created_by"] = current_user["username"]
    
    collection = service.create(collection_dict)
    
    return BaseResponse(
        success=True,
        message="Sample collection created successfully",
        data={"id": collection.id}
    )

@router.get("/sample-collections/{collection_id}", response_model=BaseResponse)
async def get_sample_collection(collection_id: int, current_user: dict = Depends(get_current_user)):
    service = SampleCollectionService()
    collection_data = service.get_collection_with_items(collection_id, current_user["tenant_id"])
    
    if not collection_data:
        raise HTTPException(status_code=404, detail="Sample collection not found")
    
    return BaseResponse(
        success=True,
        message="Sample collection retrieved successfully",
        data=collection_data
    )

@router.put("/sample-collections/{collection_id}", response_model=BaseResponse)
async def update_sample_collection(collection_id: int, collection_data: SampleCollectionUpdateSchema, current_user: dict = Depends(get_current_user)):
    service = SampleCollectionService()
    collection_dict = collection_data.dict(exclude_unset=True)
    collection_dict["updated_by"] = current_user["username"]
    
    collection = service.update(collection_id, collection_dict, current_user["tenant_id"])
    
    if not collection:
        raise HTTPException(status_code=404, detail="Sample collection not found")
    
    return BaseResponse(success=True, message="Sample collection updated successfully")

@router.delete("/sample-collections/{collection_id}", response_model=BaseResponse)
async def delete_sample_collection(collection_id: int, current_user: dict = Depends(get_current_user)):
    service = SampleCollectionService()
    success = service.delete(collection_id, current_user["tenant_id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Sample collection not found")
    
    return BaseResponse(success=True, message="Sample collection deleted successfully")
