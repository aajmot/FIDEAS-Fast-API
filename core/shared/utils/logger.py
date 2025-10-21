import logging
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class LogService:
    _instance: Optional['LogService'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        log_level = os.getenv('LOG_LEVEL', 'DEBUG')
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = f"{log_dir}/app_{datetime.now().strftime('%Y%m%d')}.log"
        
        app_name = os.getenv('APP_NAME', 'FIDEAS-Enterprise Management Tool')
        self._logger = logging.getLogger(app_name)
        self._logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler - ensure it shows all levels
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def info(self, message: str, module: str = None):
        log_msg = f"[{module or 'UNKNOWN'}] {message}"
        self._logger.info(log_msg)
        print(f"INFO: {log_msg}")  # Ensure console output
    
    def error(self, message: str, module: str = None, exc_info=None):
        log_msg = f"[{module or 'UNKNOWN'}] {message}"
        self._logger.error(log_msg, exc_info=exc_info)
        print(f"ERROR: {log_msg}")  # Ensure console output
    
    def warning(self, message: str, module: str = None):
        log_msg = f"[{module or 'UNKNOWN'}] {message}"
        self._logger.warning(log_msg)
        print(f"WARNING: {log_msg}")  # Ensure console output
    
    def debug(self, message: str, module: str = None):
        log_msg = f"[{module or 'UNKNOWN'}] {message}"
        self._logger.debug(log_msg)
        print(f"DEBUG: {log_msg}")  # Ensure console output

logger = LogService()