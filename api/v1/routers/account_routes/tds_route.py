from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()


@router.get("/tds-sections", response_model=PaginatedResponse)
async def get_tds_sections(current_user: dict = Depends(get_current_user)):
    """Get all TDS sections"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT id, section_code, description, rate, threshold_limit, is_active
            FROM tds_sections
            WHERE tenant_id = :tenant_id
            ORDER BY section_code
        """), {"tenant_id": current_user['tenant_id']})

        sections = [{
            "id": r[0],
            "section_code": r[1],
            "description": r[2],
            "rate": float(r[3]),
            "threshold_limit": float(r[4]),
            "is_active": r[5]
        } for r in result]

        return PaginatedResponse(
            success=True,
            message="TDS sections retrieved successfully",
            data=sections,
            total=len(sections),
            page=1,
            per_page=len(sections),
            total_pages=1
        )


@router.post("/tds-sections", response_model=BaseResponse)
async def create_tds_section(section_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create TDS section"""
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO tds_sections (section_code, description, rate, threshold_limit, tenant_id)
                VALUES (:code, :description, :rate, :threshold, :tenant_id)
                RETURNING id
            """), {
                "code": section_data['section_code'],
                "description": section_data['description'],
                "rate": section_data['rate'],
                "threshold": section_data.get('threshold_limit', 0),
                "tenant_id": current_user['tenant_id']
            })

            section_id = result.fetchone()[0]
            session.commit()

            return BaseResponse(
                success=True,
                message="TDS section created successfully",
                data={"id": section_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/tds-calculate", response_model=BaseResponse)
async def calculate_tds(calc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Calculate TDS amount"""
    with db_manager.get_session() as session:
        section = session.execute(text("""
            SELECT rate, threshold_limit FROM tds_sections
            WHERE section_code = :code AND tenant_id = :tenant_id
        """), {"code": calc_data['section_code'], "tenant_id": current_user['tenant_id']}).fetchone()

        if not section:
            raise HTTPException(status_code=404, detail="TDS section not found")

        amount = calc_data['amount']
        rate = float(section[0])
        threshold = float(section[1])

        tds_amount = (amount * rate / 100) if amount >= threshold else 0

        return BaseResponse(
            success=True,
            message="TDS calculated successfully",
            data={
                "amount": amount,
                "rate": rate,
                "threshold": threshold,
                "tds_amount": tds_amount,
                "net_amount": amount - tds_amount
            }
        )
