# backend/core/config.py

import os
import sys
from pathlib import Path
# Use absolute import instead of relative
from app.utils.user_utils import get_user_base_path, validate_db_path

# Define app mode based on environment variable or auto-detection
APP_MODE = os.environ.get("APP_MODE", "auto").lower()  # 'home', 'office', or 'auto'

# Path to local database (for home mode)
LOCAL_DB_PATH = Path(__file__).parent.parent / "data" / "401k_payments.db"

# Get base path (for office mode)
BASE_PATH = get_user_base_path()
OFFICE_DB_PATH = BASE_PATH / "HohimerPro" / "database" / "401k_payments.db"

# Determine which database to use based on mode and availability
if APP_MODE == "home":
    DB_PATH = LOCAL_DB_PATH
elif APP_MODE == "office":
    DB_PATH = OFFICE_DB_PATH
else:  # Auto-detect based on file availability
    if OFFICE_DB_PATH.exists():
        print("Auto-detected OFFICE mode - using OneDrive database")
        DB_PATH = OFFICE_DB_PATH
        APP_MODE = "office"
    else:
        print("Auto-detected HOME mode - using local database")
        DB_PATH = LOCAL_DB_PATH
        APP_MODE = "home"

DB_BACKUP_PATH = (BASE_PATH / "HohimerPro" / "database" / "db_backups" 
                  if APP_MODE == "office" else Path(__file__).parent.parent / "data" / "backup_dbs")

# Validate the database path to provide early and clear feedback
try:
    validate_db_path(DB_PATH)
    print(f"Successfully connected to database at: {DB_PATH}")
    print(f"Running in {APP_MODE.upper()} mode")
except (FileNotFoundError, Exception) as e:
    print(f"ERROR: {str(e)}")
    print(f"Failed to access database at: {DB_PATH}")
    
    # If in auto mode and first attempt failed, try the alternative
    if APP_MODE == "auto" and DB_PATH == OFFICE_DB_PATH:
        print("Attempting to use local database instead...")
        DB_PATH = LOCAL_DB_PATH
        APP_MODE = "home"
        try:
            validate_db_path(DB_PATH)
            print(f"Successfully connected to database at: {DB_PATH}")
            print(f"Running in {APP_MODE.upper()} mode")
        except (FileNotFoundError, Exception) as e2:
            print(f"ERROR: {str(e2)}")
            print("Unable to connect to either office or home database")
    elif APP_MODE == "auto" and DB_PATH == LOCAL_DB_PATH:
        print("Attempting to use office database instead...")
        DB_PATH = OFFICE_DB_PATH
        APP_MODE = "office"
        try:
            validate_db_path(DB_PATH)
            print(f"Successfully connected to database at: {DB_PATH}")
            print(f"Running in {APP_MODE.upper()} mode")
        except (FileNotFoundError, Exception) as e2:
            print(f"ERROR: {str(e2)}")
            print("Unable to connect to either office or home database")

PATHS = {
    'BASE_PATH': BASE_PATH,
    'DB_PATH': DB_PATH,
    'DB_BACKUP_PATH': DB_BACKUP_PATH,
    'APP_MODE': APP_MODE,
}

ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:6069",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:6069",
]

# Application metadata
APP_NAME = "HohimerPro - 401K Payments"
APP_VERSION = "1.0"
