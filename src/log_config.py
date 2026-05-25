import logging
import sys
import os
from datetime import datetime
import structlog
from .config import get_config

def setup_logging():
    config = get_config()
    log_level_str = config.logging.get("level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Ensure logs directory exists
    logs_dir = config.paths.get("logs_dir", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"collector_{date_str}.log")

    # Set up standard logging
    handlers = []
    
    if config.logging.get("console", True):
        handlers.append(logging.StreamHandler(sys.stdout))
        
    if config.logging.get("file", True):
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
    )

    # Configure structlog
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.logging.get("json_format", False):
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger(__name__)
    logger.info("Logging initialized", log_file=log_file, level=log_level_str)
