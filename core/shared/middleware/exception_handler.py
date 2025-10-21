from functools import wraps
from typing import Callable, Any
from core.shared.utils.logger import logger

class ExceptionMiddleware:
    @staticmethod
    def handle_exceptions(module_name: str = None):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = f"Error in {func.__name__}: {str(e)}"
                    logger.error(error_msg, module_name, exc_info=True)
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def safe_execute(func: Callable, *args, default_return=None, module_name: str = None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Safe execution failed in {func.__name__}: {str(e)}"
            logger.error(error_msg, module_name, exc_info=True)
            return default_return