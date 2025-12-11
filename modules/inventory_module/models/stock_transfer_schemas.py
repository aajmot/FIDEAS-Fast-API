from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class StockTransferItemCreate(BaseModel):
    line_no: int = Field(..., description="Line number")
    product_id: int = Field(..., description="Product ID")
    batch_number: Optional[str] = Field(None, description="Batch number")
    quantity: Decimal = Field(..., gt=0, description="Transfer quantity")
    uom: str = Field("NOS", description="Unit of measure")
    unit_cost_base: Decimal = Field(..., ge=0, description="Unit cost in base currency")
    currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    unit_cost_foreign: Optional[Decimal] = Field(None, description="Unit cost in foreign currency")
    exchange_rate: Optional[Decimal] = Field(1, description="Exchange rate")
    reason: Optional[str] = Field(None, description="Item-level reason")

class StockTransferCreate(BaseModel):
    transfer_number: Optional[str] = Field(None, description="Transfer number (auto-generated if not provided)")
    from_warehouse_id: int = Field(..., description="Source warehouse ID")
    to_warehouse_id: int = Field(..., description="Destination warehouse ID")
    transfer_date: Optional[datetime] = Field(None, description="Transfer date")
    transfer_type: str = Field(..., description="Transfer type: INTERNAL, INTERCOMPANY, RETURN")
    reason: Optional[str] = Field(None, description="Transfer reason")
    currency_id: Optional[int] = Field(None, description="Currency ID")
    exchange_rate: Optional[Decimal] = Field(1, description="Exchange rate")
    status: Optional[str] = Field("DRAFT", description="Status: DRAFT, APPROVED, IN_TRANSIT, COMPLETED, CANCELLED")
    items: List[StockTransferItemCreate] = Field(..., description="Transfer items")
    
    @validator('transfer_type')
    def validate_transfer_type(cls, v):
        if v not in ['INTERNAL', 'INTERCOMPANY', 'RETURN']:
            raise ValueError('Transfer type must be INTERNAL, INTERCOMPANY, or RETURN')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['DRAFT', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Status must be DRAFT, APPROVED, IN_TRANSIT, COMPLETED, or CANCELLED')
        return v
    
    @validator('from_warehouse_id', 'to_warehouse_id')
    def validate_warehouse_ids(cls, v):
        if v <= 0:
            raise ValueError('Warehouse ID must be positive')
        return v

class StockTransferItemResponse(BaseModel):
    id: int
    line_no: int
    product_id: int
    product_name: Optional[str]
    batch_number: Optional[str]
    quantity: Decimal
    uom: str
    from_stock_before: Decimal
    from_stock_after: Decimal
    to_stock_before: Decimal
    to_stock_after: Decimal
    unit_cost_base: Decimal
    total_cost_base: Decimal
    currency_id: Optional[int]
    unit_cost_foreign: Optional[Decimal]
    total_cost_foreign: Optional[Decimal]
    exchange_rate: Decimal
    reason: Optional[str]

class StockTransferResponse(BaseModel):
    id: int
    transfer_number: str
    from_warehouse_id: int
    from_warehouse_name: Optional[str]
    to_warehouse_id: int
    to_warehouse_name: Optional[str]
    transfer_date: datetime
    transfer_type: str
    reason: Optional[str]
    total_items: int
    total_quantity: Decimal
    total_cost_base: Decimal
    currency_id: Optional[int]
    exchange_rate: Decimal
    status: str
    approval_request_id: Optional[int]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    from_voucher_id: Optional[int]
    to_voucher_id: Optional[int]
    is_active: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    items: List[StockTransferItemResponse]
    
    class Config:
        from_attributes = True