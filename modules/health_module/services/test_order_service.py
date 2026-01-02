from core.database.connection import db_manager
from modules.health_module.models.test_order_entity import TestOrder, TestOrderItem
from core.shared.utils.logger import logger
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
import math

class TestOrderService:
    def __init__(self):
        self.logger_name = "TestOrderService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                order = TestOrder(**data)
                session.add(order)
                session.flush()
                
                if items:
                    for item in items:
                        item['test_order_id'] = order.id
                        item['tenant_id'] = data['tenant_id']
                        order_item = TestOrderItem(**item)
                        session.add(order_item)
                
                order_id = order.id
                logger.info(f"Test order created: {order.test_order_number}", self.logger_name)
                session.expunge(order)
                order.id = order_id
                return order
        except Exception as e:
            logger.error(f"Error creating test order: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                orders = query.all()
                for order in orders:
                    session.expunge(order)
                return orders
        except Exception as e:
            logger.error(f"Error fetching test orders: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.id == order_id, TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                order = query.first()
                if order:
                    session.expunge(order)
                return order
        except Exception as e:
            logger.error(f"Error fetching test order: {str(e)}", self.logger_name)
            return None
    
    def update(self, order_id, data, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.id == order_id, TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                order = query.first()
                
                if not order:
                    raise HTTPException(status_code=404, detail="Test order not found")
                
                if order.status in ['COMPLETED', 'REPORTED'] and 'status' not in data:
                    raise HTTPException(status_code=400, detail="Cannot modify completed or reported orders")
                
                items = data.pop('items', None)
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'created_by', 'tenant_id']:
                        setattr(order, key, value)
                order.updated_at = datetime.utcnow()
                
                if items is not None:
                    if items:
                        session.query(TestOrderItem).filter(TestOrderItem.test_order_id == order_id).update({'is_deleted': True})
                        session.flush()
                        for item in items:
                            item.pop('id', None)
                            item['test_order_id'] = order_id
                            item['tenant_id'] = order.tenant_id
                            order_item = TestOrderItem(**item)
                            session.add(order_item)
                    else:
                        session.query(TestOrderItem).filter(TestOrderItem.test_order_id == order_id).update({'is_deleted': True})
                
                session.flush()
                logger.info(f"Test order updated: {order.test_order_number}", self.logger_name)
                session.expunge(order)
                return order
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating test order: {str(e)}", self.logger_name)
            raise
    
    def delete(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.id == order_id, TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                order = query.first()
                
                if not order:
                    raise HTTPException(status_code=404, detail="Test order not found")
                
                if order.status in ['COMPLETED', 'REPORTED']:
                    raise HTTPException(status_code=400, detail="Cannot delete completed or reported orders")
                
                order.is_deleted = True
                order.updated_at = datetime.utcnow()
                session.query(TestOrderItem).filter(TestOrderItem.test_order_id == order_id).update({'is_deleted': True})
                logger.info(f"Test order deleted: {order.test_order_number}", self.logger_name)
                return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting test order: {str(e)}", self.logger_name)
            raise
    
    def get_items(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrderItem).filter(
                    TestOrderItem.test_order_id == order_id,
                    TestOrderItem.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestOrderItem.tenant_id == tenant_id)
                items = query.all()
                for item in items:
                    session.expunge(item)
                return items
        except Exception as e:
            logger.error(f"Error fetching test order items: {str(e)}", self.logger_name)
            return []
    
    def get_paginated(self, tenant_id, page, per_page, search=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(
                    TestOrder.tenant_id == tenant_id,
                    TestOrder.is_deleted == False
                ).order_by(TestOrder.id.desc())
                
                if search:
                    query = query.filter(or_(
                        TestOrder.test_order_number.ilike(f"%{search}%"),
                        TestOrder.patient_name.ilike(f"%{search}%"),
                        TestOrder.doctor_name.ilike(f"%{search}%")
                    ))
                
                total = query.count()
                offset = (page - 1) * per_page
                orders = query.offset(offset).limit(per_page).all()
                
                order_data = [{
                "id": order.id,
                "test_order_number": order.test_order_number,
                "appointment_id": order.appointment_id,
                "patient_id": order.patient_id,
                "patient_name": order.patient_name,
                "patient_phone": order.patient_phone,
                "doctor_id": order.doctor_id,
                "doctor_name": order.doctor_name,
                "doctor_phone": order.doctor_phone,
                "doctor_license_number": order.doctor_license_number,
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "status": order.status,
                "urgency": order.urgency,
                "notes": order.notes,
                "tags": order.tags,
                "agency_id": order.agency_id,
                "subtotal_amount": float(order.subtotal_amount) if order.subtotal_amount else None,
                "items_total_discount_amount": float(order.items_total_discount_amount) if order.items_total_discount_amount else None,
                "taxable_amount": float(order.taxable_amount) if order.taxable_amount else None,
                "cgst_amount": float(order.cgst_amount) if order.cgst_amount else None,
                "sgst_amount": float(order.sgst_amount) if order.sgst_amount else None,
                "igst_amount": float(order.igst_amount) if order.igst_amount else None,
                "cess_amount": float(order.cess_amount) if order.cess_amount else None,
                "overall_disc_percentage": float(order.overall_disc_percentage) if order.overall_disc_percentage else None,
                "overall_disc_amount": float(order.overall_disc_amount) if order.overall_disc_amount else None,
                "overall_cess_percentage": float(order.overall_cess_percentage) if order.overall_cess_percentage else None,
                "overall_cess_amount": float(order.overall_cess_amount) if order.overall_cess_amount else None,
                "roundoff": float(order.roundoff) if order.roundoff else None,
                "final_amount": float(order.final_amount) if order.final_amount else None,
                "is_active": order.is_active,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "created_by": order.created_by,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "updated_by": order.updated_by,
                } for order in orders]
                
                return {
                    "data": order_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": math.ceil(total / per_page)
                }
        except Exception as e:
            logger.error(f"Error fetching paginated test orders: {str(e)}", self.logger_name)
            raise
    
    def get_order_with_items(self, order_id, tenant_id):
        try:
            order = self.get_by_id(order_id, tenant_id)
            if not order:
                return None
            
            items = self.get_items(order_id, tenant_id)
            
            return {
                "id": order.id,
                "test_order_number": order.test_order_number,
                "appointment_id": order.appointment_id,
                "patient_id": order.patient_id,
                "patient_name": order.patient_name,
                "patient_phone": order.patient_phone,
                "doctor_id": order.doctor_id,
                "doctor_name": order.doctor_name,
                "doctor_phone": order.doctor_phone,
                "doctor_license_number": order.doctor_license_number,
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "status": order.status,
                "urgency": order.urgency,
                "notes": order.notes,
                "tags": order.tags,
                "agency_id": order.agency_id,
                "subtotal_amount": float(order.subtotal_amount) if order.subtotal_amount else None,
                "items_total_discount_amount": float(order.items_total_discount_amount) if order.items_total_discount_amount else None,
                "taxable_amount": float(order.taxable_amount) if order.taxable_amount else None,
                "cgst_amount": float(order.cgst_amount) if order.cgst_amount else None,
                "sgst_amount": float(order.sgst_amount) if order.sgst_amount else None,
                "igst_amount": float(order.igst_amount) if order.igst_amount else None,
                "cess_amount": float(order.cess_amount) if order.cess_amount else None,
                "overall_disc_percentage": float(order.overall_disc_percentage) if order.overall_disc_percentage else None,
                "overall_disc_amount": float(order.overall_disc_amount) if order.overall_disc_amount else None,
                "overall_cess_percentage": float(order.overall_cess_percentage) if order.overall_cess_percentage else None,
                "overall_cess_amount": float(order.overall_cess_amount) if order.overall_cess_amount else None,
                "roundoff": float(order.roundoff) if order.roundoff else None,
                "final_amount": float(order.final_amount) if order.final_amount else None,
                "is_active": order.is_active,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "created_by": order.created_by,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "updated_by": order.updated_by,
                "items": [{
                    "id": item.id,
                    "line_no": item.line_no,
                    "test_id": item.test_id,
                    "test_name": item.test_name,
                    "panel_id": item.panel_id,
                    "panel_name": item.panel_name,
                    "rate": float(item.rate) if item.rate else None,
                    "disc_percentage": float(item.disc_percentage) if item.disc_percentage else None,
                    "disc_amount": float(item.disc_amount) if item.disc_amount else None,
                    "taxable_amount": float(item.taxable_amount) if item.taxable_amount else None,
                    "cgst_rate": float(item.cgst_rate) if item.cgst_rate else None,
                    "cgst_amount": float(item.cgst_amount) if item.cgst_amount else None,
                    "sgst_rate": float(item.sgst_rate) if item.sgst_rate else None,
                    "sgst_amount": float(item.sgst_amount) if item.sgst_amount else None,
                    "igst_rate": float(item.igst_rate) if item.igst_rate else None,
                    "igst_amount": float(item.igst_amount) if item.igst_amount else None,
                    "cess_rate": float(item.cess_rate) if item.cess_rate else None,
                    "cess_amount": float(item.cess_amount) if item.cess_amount else None,
                    "total_amount": float(item.total_amount) if item.total_amount else None,
                    "item_status": item.item_status,
                    "remarks": item.remarks
                } for item in items]
            }
        except Exception as e:
            logger.error(f"Error fetching test order with items: {str(e)}", self.logger_name)
            raise
    
    def create_with_accounting(self, data, username, tenant_id):
        try:
            order = self.create(data)
            
            # Post to accounting
            try:
                from modules.account_module.services.transaction_posting_service import TransactionPostingService
                with db_manager.get_session() as session:
                    posting_data = {
                        'reference_type': 'DIAGNOSTIC_ORDER',
                        'reference_id': order.id,
                        'reference_number': order.test_order_number,
                        'total_amount': float(order.final_amount) if order.final_amount else 0,
                        'transaction_date': order.order_date,
                        'created_by': username
                    }
                    TransactionPostingService.post_transaction(
                        session, 'DIAGNOSTIC_SALES', posting_data, tenant_id
                    )
                    session.commit()
            except Exception as e:
                logger.error(f"Accounting posting failed for diagnostic order: {str(e)}", self.logger_name)
            
            return order
        except Exception as e:
            logger.error(f"Error creating test order with accounting: {str(e)}", self.logger_name)
            raise
