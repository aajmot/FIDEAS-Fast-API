from typing import Any, Optional, Dict
from fastapi import status
from fastapi.responses import JSONResponse


class APIResponse:
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """Create successful API response"""
        response_data = {
            "success": True,
            "message": message,
            "data": data
        }
        return JSONResponse(content=response_data, status_code=status_code)
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        errors: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> JSONResponse:
        """Create error API response"""
        response_data = {
            "success": False,
            "message": message,
            "errors": errors
        }
        return JSONResponse(content=response_data, status_code=status_code)
    
    @staticmethod
    def created(data: Any = None, message: str = "Created successfully") -> JSONResponse:
        """Create 201 Created response"""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> JSONResponse:
        """Create 404 Not Found response"""
        return APIResponse.error(message, status_code=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> JSONResponse:
        """Create 401 Unauthorized response"""
        return APIResponse.error(message, status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def forbidden(message: str = "Forbidden") -> JSONResponse:
        """Create 403 Forbidden response"""
        return APIResponse.error(message, status_code=status.HTTP_403_FORBIDDEN)