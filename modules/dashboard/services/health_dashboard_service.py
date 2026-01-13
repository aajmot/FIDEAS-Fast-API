from datetime import datetime
from sqlalchemy import text
from typing import Dict, List
from core.database.connection import db_manager

class HealthDashboardService:
    """Service for health module dashboard analytics using actual health data"""

    @staticmethod
    def get_patient_analytics(tenant_id: int) -> Dict:
        """Get patient analytics using stored procedure"""
        with db_manager.get_session() as session:
            results = session.execute(
                text("SELECT * FROM get_patient_analytics(:tenant_id)"),
                {"tenant_id": tenant_id}
            ).fetchall()

            if not results:
                return {"total_patients": 0, "new_patients_month": 0, "active_patients": 0, 
                       "age_groups": [], "gender_distribution": []}

            # Extract basic stats from first row
            total_patients = results[0][0]
            new_patients_month = results[0][1] 
            active_patients = results[0][2]

            # Group age and gender data
            age_groups = {}
            gender_distribution = {}
            
            for row in results:
                if row[3] and row[4]:  # age_group and age_count
                    age_groups[row[3]] = row[4]
                if row[5] and row[6]:  # gender and gender_count
                    gender_distribution[row[5]] = row[6]

            return {
                "total_patients": total_patients,
                "new_patients_month": new_patients_month,
                "active_patients": active_patients,
                "age_groups": [{"group": k, "count": v} for k, v in age_groups.items()],
                "gender_distribution": [{"gender": k, "count": v} for k, v in gender_distribution.items()]
            }

    @staticmethod
    def get_appointment_analytics(tenant_id: int) -> Dict:
        """Get appointment analytics using stored procedure"""
        with db_manager.get_session() as session:
            result = session.execute(
                text("SELECT * FROM get_appointment_analytics(:tenant_id)"),
                {"tenant_id": tenant_id}
            ).fetchone()

            return {
                "total_appointments": int(result[0]) if result else 0,
                "scheduled": int(result[1]) if result else 0,
                "completed": int(result[2]) if result else 0,
                "cancelled": int(result[3]) if result else 0,
                "no_show": int(result[4]) if result else 0,
                "completion_rate": float(result[5]) if result else 0,
                "no_show_rate": float(result[6]) if result else 0,
                "avg_daily_appointments": float(result[7]) if result else 0
            }

    @staticmethod
    def get_clinical_operations(tenant_id: int) -> Dict:
        """Get clinical operations metrics using stored procedure"""
        with db_manager.get_session() as session:
            result = session.execute(
                text("SELECT * FROM get_clinical_operations(:tenant_id)"),
                {"tenant_id": tenant_id}
            ).fetchone()

            return {
                "medical_records_generated": int(result[0]) if result else 0,
                "prescriptions_issued": int(result[1]) if result else 0,
                "test_orders_created": int(result[2]) if result else 0,
                "sample_collections": int(result[3]) if result else 0,
                "test_results_completed": int(result[4]) if result else 0,
                "avg_turnaround_hours": float(result[5]) if result else 0
            }

    @staticmethod
    def get_doctor_performance(tenant_id: int) -> List[Dict]:
        """Get doctor performance metrics using stored procedure"""
        with db_manager.get_session() as session:
            results = session.execute(
                text("SELECT * FROM get_doctor_performance(:tenant_id)"),
                {"tenant_id": tenant_id}
            ).fetchall()

            return [
                {
                    "doctor_name": row[0],
                    "specialization": row[1],
                    "total_appointments": int(row[2]),
                    "completed_appointments": int(row[3]),
                    "consultation_fee": float(row[4]) if row[4] else 0,
                    "completion_rate": round((int(row[3]) / int(row[2]) * 100), 2) if int(row[2]) > 0 else 0
                }
                for row in results
            ]

    @staticmethod
    def get_test_analytics(tenant_id: int) -> List[Dict]:
        """Get test analytics using stored procedure"""
        with db_manager.get_session() as session:
            results = session.execute(
                text("SELECT * FROM get_test_analytics(:tenant_id)"),
                {"tenant_id": tenant_id}
            ).fetchall()

            return [
                {
                    "test_name": row[0],
                    "category": row[1],
                    "total_orders": int(row[2]),
                    "revenue": float(row[3]),
                    "avg_turnaround_days": float(row[4])
                }
                for row in results
            ]