from fastapi import APIRouter, HTTPException
from api.schemas.common import BaseResponse
from modules.health_module.services.test_result_service import TestResultService
from core.shared.utils.crypto_utils import crypto_utils
from core.shared.utils.barcode_utils import BarcodeGenerator
from core.shared.utils.logger import logger

router = APIRouter()

@router.get("/test-results/{encrypted_result_no}", response_model=BaseResponse)
async def get_public_test_result(encrypted_result_no: str):
    """
    Public endpoint to fetch test result by encrypted result_no.
    Decrypts the result_no and returns result details with barcode.
    """
    try:
        # Decrypt result_no
        result_number = crypto_utils.decrypt(encrypted_result_no)
        
        if not result_number:
            raise HTTPException(
                status_code=400,
                detail={
                    "header": "Invalid Access Link",
                    "message": "The test result link is invalid or has expired. Please contact your healthcare provider for a new link.",
                    "action": "Contact Support"
                }
            )
        
        # Fetch result with barcode
        service = TestResultService()
        result = service.get_by_result_number(result_number)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "header": "Test Result Not Found",
                    "message": "We couldn't find the test result you're looking for. It may have been removed or is no longer available.",
                    "action": "Verify Link"
                }
            )
        
        # Get details and files
        details = service.get_details(result.id)
        files = service.get_files(result.id)
        
        # Extract tenant and test_order data
        tenant = getattr(result, 'tenant', None)
        test_order = getattr(result, 'test_order', None)
        
        # Generate QR code
        qr_code = None
        try:
            qr_data = crypto_utils.generate_test_result_url(result.result_number)
            qr_code = BarcodeGenerator.generate_qr_code(qr_data)
        except Exception as qr_error:
            logger.error(f"QR code generation failed: {str(qr_error)}", "PublicTestResultRoute")
        
        return BaseResponse(
            success=True,
            message="Your test results are ready for viewing",
            data={
                "header": "Test Results Available",
                "tenant": {
                    "name": tenant.name if tenant else None,
                    "code": tenant.code if tenant else None,
                    "logo": tenant.logo if tenant else None,
                    "tagline": tenant.tagline if tenant else None,
                    "address": tenant.address if tenant else None
                } if tenant else None,
                "test_order": {
                    "id": test_order.id if test_order else None,
                    "test_order_number": test_order.test_order_number if test_order else None,
                    "order_date": test_order.order_date.isoformat() if test_order and test_order.order_date else None,
                    "patient_name": test_order.patient_name if test_order else None,
                    "patient_phone": test_order.patient_phone if test_order else None,
                    "doctor_name": test_order.doctor_name if test_order else None,
                    "doctor_phone": test_order.doctor_phone if test_order else None,
                    "doctor_license_number": test_order.doctor_license_number if test_order else None,
                    "urgency": test_order.urgency if test_order else None,
                    "status": test_order.status if test_order else None
                } if test_order else None,
                "result": {
                    "id": result.id,
                    "result_number": result.result_number,
                    "result_date": result.result_date.isoformat() if result.result_date else None,
                    "overall_report": result.overall_report,
                    "performed_by": result.performed_by,
                    "result_type": result.result_type,
                    "notes": result.notes,
                    "license_number": result.license_number,
                    "qr_code": qr_code,
                    "details": [{
                        "parameter_name": detail.parameter_name,
                        "unit": detail.unit,
                        "parameter_value": detail.parameter_value,
                        "reference_value": detail.reference_value,
                        "verdict": detail.verdict,
                        "notes": detail.notes
                    } for detail in details],
                    "files": [{
                        "file_name": file.file_name,
                        "file_path": file.file_path,
                        "file_format": file.file_format,
                        "file_size": file.file_size,
                        "description": file.description
                    } for file in files]
                },
                "action": "View Results"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in public test result endpoint: {str(e)}", "PublicTestResultRoute")
        raise HTTPException(
            status_code=500,
            detail={
                "header": "Service Unavailable",
                "message": "We're experiencing technical difficulties. Please try again later or contact support if the issue persists.",
                "action": "Retry Later"
            }
        )
