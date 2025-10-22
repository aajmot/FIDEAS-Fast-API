from fastapi import APIRouter
from app.api.v1.controllers.clinic.patient_controller import router as patient_router
from app.api.v1.controllers.clinic.appointment_controller import router as appointment_router

router = APIRouter()

# Include all clinic controllers
router.include_router(patient_router, tags=["Clinic - Patients"])
router.include_router(appointment_router, tags=["Clinic - Appointments"])