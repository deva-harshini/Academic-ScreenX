import sys
import os
from pathlib import Path

# Add project root directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure current working directory has project root
try:
    os.chdir(str(BASE_DIR))
except Exception:
    pass

from app.main import app

# Expose both app and handler for complete Vercel and AWS Lambda compatibility
handler = app
