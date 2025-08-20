import logging
from pathlib import Path

# Create logging file
log_file = Path('./logs/logging.txt')
if not log_file.exists():
    log_file.parent.mkdir(parents=True, exist_ok=True) 
    log_file.touch()
    print("Logigng file created:", log_file)

# Configure logging level
logging_str = "%(asctime)s: %(levelname)s: %(module)s: %(message)s"
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG, 
    format=logging_str
   )
logger = logging.getLogger("ChatGPT-ZaloOA")