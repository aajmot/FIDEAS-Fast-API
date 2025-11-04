from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ProductWasteItemRequest(BaseModel):
    """Schema for individual waste line item"""
    line_no: int = Field(..., description="Line number (sequential)")
    product_id: int = Field(..., description="Product being wasted")
    batch_number: Optional[str] = Field(None, max_length=50, description="Batch number if applicable")
    quantity: Decimal = Field(..., gt=0, description="Quantity wasted")
    unit_cost_base: Decimal = Field(..., ge=0, description="Unit cost in base currency")
    
    # Optional per-item fields
    unit_cost_foreign: Optional[Decimal] = Field(None, ge=0, description="Unit cost in foreign currency")
    reason: Optional[str] = Field(None, max_length=500, description="Item-specific reason (overrides header)")
    
    class Config:
        from_attributes = True


class ProductWasteRequest(BaseModel):
    """Schema for creating product waste records with multiple items"""
    
    # Header fields - Required
    waste_number: str = Field(..., max_length=50, description="Unique waste reference number")
    waste_date: datetime = Field(..., description="Date of waste occurrence")
    reason: str = Field(..., max_length=500, description="General reason for waste")
    
    # Header fields - Optional
    warehouse_id: Optional[int] = Field(None, description="Warehouse where waste occurred")
    currency_id: Optional[int] = Field(None, description="Currency ID (defaults to tenant's base currency)")
    voucher_id: Optional[int] = Field(None, description="Linked accounting voucher")
    is_active: bool = Field(True, description="Active status")
    
    # Line items - Required (at least one item)
    items: List[ProductWasteItemRequest] = Field(..., min_length=1, description="List of waste items")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "warehouse_id": 1,
                "waste_number": "WST-2025-001",
                "waste_date": "2025-11-04T10:30:00",
                "reason": "Monthly expired products disposal",
                "currency_id": 1,
                "is_active": True,
                "items": [
                    {
                        "line_no": 1,
                        "product_id": 100,
                        "batch_number": "BATCH-001",
                        "quantity": 5.0,
                        "unit_cost_base": 150.00,
                        "reason": "Expired"
                    },
                    {
                        "line_no": 2,
                        "product_id": 101,
                        "batch_number": "BATCH-002",
                        "quantity": 3.0,
                        "unit_cost_base": 200.00,
                        "reason": "Damaged packaging"
                    }
                ]
            }
        }
    
    @validator('waste_date', pre=True)
    def parse_waste_date(cls, v):
        """Allow various date formats"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @validator('items')
    def validate_items(cls, v):
        """Ensure at least one item and unique line numbers"""
        if not v or len(v) == 0:
            raise ValueError('At least one waste item is required')
        
        line_numbers = [item.line_no for item in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError('Line numbers must be unique')
        
        return v
    



class ProductWasteItemResponse(BaseModel):
    """Schema for waste line item response"""
    id: int
    line_no: int
    product_id: int
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: Decimal
    unit_cost_base: Decimal
    total_cost_base: Decimal
    currency_id: Optional[int] = None
    unit_cost_foreign: Optional[Decimal] = None
    total_cost_foreign: Optional[Decimal] = None
    exchange_rate: Decimal
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductWasteResponse(BaseModel):
    """Schema for product waste header response"""
    id: int
    waste_number: str
    warehouse_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    waste_date: datetime
    reason: str
    total_quantity: Decimal
    total_cost_base: Decimal
    total_cost_foreign: Optional[Decimal] = None
    currency_id: Optional[int] = None
    exchange_rate: Decimal
    voucher_id: Optional[int] = None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    items: Optional[List[ProductWasteItemResponse]] = None
    
    class Config:
        from_attributes = True
