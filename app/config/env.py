import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with optional default value"""
    return os.getenv(key, default)

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default