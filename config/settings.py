"""Application configuration settings"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fideas_db')

# Application Configuration
APP_NAME = os.getenv('APP_NAME', 'FIDEAS-Enterprise Management Tool')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

# UI Configuration
THEME = os.getenv('THEME', 'blue')
APPEARANCE_MODE = os.getenv('APPEARANCE_MODE', 'light')