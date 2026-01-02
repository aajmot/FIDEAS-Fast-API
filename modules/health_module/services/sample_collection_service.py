from core.database.connection import db_manager
from modules.health_module.models.sample_collection_entity import SampleCollection, SampleCollectionItem
from core.shared.utils.logger import logger
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
import math

class SampleCollectionService:
    def __init__(self):
        self.logger_name = "SampleCollectionService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                collection = SampleCollection(**data)
                session.add(collection)
                session.flush()
                
                if items:
                    for item in items:
                        item['collection_id'] = collection.id
                        item['tenant_id'] = data['tenant_id']
                        collection_item = SampleCollectionItem(**item)
                        session.add(collection_item)
                
                collection_id = collection.id
                logger.info(f"Sample collection created: {collection.collection_number}", self.logger_name)
                session.expunge(collection)
                collection.id = collection_id
                return collection
        except Exception as e:
            logger.error(f"Error creating sample collection: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollection).filter(SampleCollection.is_deleted == False)
                if tenant_id:
                    query = query.filter(SampleCollection.tenant_id == tenant_id)
                collections = query.all()
                for collection in collections:
                    session.expunge(collection)
                return collections
        except Exception as e:
            logger.error(f"Error fetching sample collections: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, collection_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollection).filter(
                    SampleCollection.id == collection_id,
                    SampleCollection.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(SampleCollection.tenant_id == tenant_id)
                collection = query.first()
                if collection:
                    session.expunge(collection)
                return collection
        except Exception as e:
            logger.error(f"Error fetching sample collection: {str(e)}", self.logger_name)
            return None
    
    def update(self, collection_id, data, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollection).filter(
                    SampleCollection.id == collection_id,
                    SampleCollection.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(SampleCollection.tenant_id == tenant_id)
                collection = query.first()
                
                if not collection:
                    raise HTTPException(status_code=404, detail="Sample collection not found")
                
                if collection.status == 'COMPLETED':
                    raise HTTPException(status_code=400, detail="Cannot modify completed collections")
                
                items = data.pop('items', None)
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'created_by', 'tenant_id', 'test_order_id', 'patient_id']:
                        setattr(collection, key, value)
                collection.updated_at = datetime.utcnow()
                
                if items is not None:
                    session.query(SampleCollectionItem).filter(
                        SampleCollectionItem.collection_id == collection_id
                    ).update({'is_deleted': True})
                    session.flush()
                    
                    for item in items:
                        item.pop('id', None)
                        item['collection_id'] = collection_id
                        item['tenant_id'] = collection.tenant_id
                        collection_item = SampleCollectionItem(**item)
                        session.add(collection_item)
                
                session.flush()
                logger.info(f"Sample collection updated: {collection.collection_number}", self.logger_name)
                session.expunge(collection)
                return collection
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating sample collection: {str(e)}", self.logger_name)
            raise
    
    def delete(self, collection_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollection).filter(
                    SampleCollection.id == collection_id,
                    SampleCollection.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(SampleCollection.tenant_id == tenant_id)
                collection = query.first()
                
                if not collection:
                    raise HTTPException(status_code=404, detail="Sample collection not found")
                
                if collection.status == 'COMPLETED':
                    raise HTTPException(status_code=400, detail="Cannot delete completed collections")
                
                collection.is_deleted = True
                collection.updated_at = datetime.utcnow()
                session.query(SampleCollectionItem).filter(
                    SampleCollectionItem.collection_id == collection_id
                ).update({'is_deleted': True})
                logger.info(f"Sample collection deleted: {collection.collection_number}", self.logger_name)
                return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting sample collection: {str(e)}", self.logger_name)
            raise
    
    def get_items(self, collection_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollectionItem).filter(
                    SampleCollectionItem.collection_id == collection_id,
                    SampleCollectionItem.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(SampleCollectionItem.tenant_id == tenant_id)
                items = query.all()
                for item in items:
                    session.expunge(item)
                return items
        except Exception as e:
            logger.error(f"Error fetching sample collection items: {str(e)}", self.logger_name)
            return []
    
    def get_paginated(self, tenant_id, page, per_page, search=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(SampleCollection).filter(
                    SampleCollection.tenant_id == tenant_id,
                    SampleCollection.is_deleted == False
                ).order_by(SampleCollection.id.desc())
                
                if search:
                    query = query.filter(or_(
                        SampleCollection.collection_number.ilike(f"%{search}%"),
                        SampleCollection.patient_name.ilike(f"%{search}%"),
                        SampleCollection.patient_phone.ilike(f"%{search}%")
                    ))
                
                total = query.count()
                offset = (page - 1) * per_page
                collections = query.offset(offset).limit(per_page).all()
                
                collection_data = [{
                    "id": c.id,
                    "collection_number": c.collection_number,
                    "collection_date": c.collection_date.isoformat() if c.collection_date else None,
                    "test_order_id": c.test_order_id,
                    "patient_id": c.patient_id,
                    "patient_name": c.patient_name,
                    "patient_phone": c.patient_phone,
                    "sample_type": c.sample_type,
                    "sample_condition": c.sample_condition,
                    "status": c.status,
                    "collector_name": c.collector_name,
                    "lab_technician_name": c.lab_technician_name,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                } for c in collections]
                
                return {
                    "data": collection_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": math.ceil(total / per_page)
                }
        except Exception as e:
            logger.error(f"Error fetching paginated sample collections: {str(e)}", self.logger_name)
            raise
    
    def get_collection_with_items(self, collection_id, tenant_id):
        try:
            collection = self.get_by_id(collection_id, tenant_id)
            if not collection:
                return None
            
            items = self.get_items(collection_id, tenant_id)
            
            return {
                "id": collection.id,
                "collection_number": collection.collection_number,
                "collection_date": collection.collection_date.isoformat() if collection.collection_date else None,
                "test_order_id": collection.test_order_id,
                "branch_id": collection.branch_id,
                "patient_id": collection.patient_id,
                "patient_name": collection.patient_name,
                "patient_phone": collection.patient_phone,
                "referring_doctor_id": collection.referring_doctor_id,
                "referring_doctor_name": collection.referring_doctor_name,
                "referring_doctor_phone": collection.referring_doctor_phone,
                "referring_doctor_license": collection.referring_doctor_license,
                "is_external_doctor": collection.is_external_doctor,
                "collector_id": collection.collector_id,
                "collector_name": collection.collector_name,
                "collector_phone": collection.collector_phone,
                "is_external_collector": collection.is_external_collector,
                "lab_technician_id": collection.lab_technician_id,
                "lab_technician_name": collection.lab_technician_name,
                "lab_technician_phone": collection.lab_technician_phone,
                "lab_technician_email": collection.lab_technician_email,
                "is_external_technician": collection.is_external_technician,
                "received_at": collection.received_at.isoformat() if collection.received_at else None,
                "sample_type": collection.sample_type,
                "collection_method": collection.collection_method,
                "collection_site": collection.collection_site,
                "container_type": collection.container_type,
                "sample_volume": float(collection.sample_volume) if collection.sample_volume else None,
                "volume_unit": collection.volume_unit,
                "sample_condition": collection.sample_condition,
                "is_fasting": collection.is_fasting,
                "fasting_hours": collection.fasting_hours,
                "status": collection.status,
                "rejection_reason": collection.rejection_reason,
                "rejected_at": collection.rejected_at.isoformat() if collection.rejected_at else None,
                "remarks": collection.remarks,
                "created_at": collection.created_at.isoformat() if collection.created_at else None,
                "created_by": collection.created_by,
                "updated_at": collection.updated_at.isoformat() if collection.updated_at else None,
                "updated_by": collection.updated_by,
                "items": [{
                    "id": item.id,
                    "line_no": item.line_no,
                    "test_order_item_id": item.test_order_item_id,
                    "test_id": item.test_id,
                    "test_name": item.test_name,
                    "required_volume": float(item.required_volume) if item.required_volume else None,
                    "collected_volume": float(item.collected_volume) if item.collected_volume else None,
                    "item_status": item.item_status,
                    "result_value": item.result_value,
                    "result_unit": item.result_unit,
                    "reference_range": item.reference_range,
                    "is_abnormal": item.is_abnormal,
                    "started_at": item.started_at.isoformat() if item.started_at else None,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                    "verified_at": item.verified_at.isoformat() if item.verified_at else None,
                    "verified_by": item.verified_by,
                    "remarks": item.remarks
                } for item in items]
            }
        except Exception as e:
            logger.error(f"Error fetching sample collection with items: {str(e)}", self.logger_name)
            raise
