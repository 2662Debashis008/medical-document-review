import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format="{time} | {level} | {message}"
)

logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)