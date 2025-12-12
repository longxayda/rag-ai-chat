import logging
import sys
logger = logging.getLogger(__name__)

def show_info_and_below(record):
    return record.levelname == "INFO"

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_format = logging.Formatter("STDOUT %(asctime)s - %(levelname)s - %(message)s")
stdout_handler.setFormatter(stdout_format)
# stdout_handler.addFilter(show_info_and_below)
logger.addHandler(stdout_handler)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
stderr_format = logging.Formatter("STDERR %(asctime)s - %(levelname)s - %(message)s")
stderr_handler.setFormatter(stderr_format)
logger.addHandler(stderr_handler)
    
