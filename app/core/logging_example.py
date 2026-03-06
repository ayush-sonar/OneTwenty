# Example usage of the logging system

from app.core.logging import logger, setup_logger

# In any module, you can create a module-specific logger
module_logger = setup_logger(__name__)

# Basic logging
logger.info("Application started")
logger.warning("This is a warning")
logger.error("This is an error")

# Logging with extra context
logger.info(
    "User action performed",
    extra={
        'extra_data': {
            'user_id': 123,
            'action': 'login',
            'ip_address': '192.168.1.1'
        }
    }
)

# In request handlers, the request_id is automatically set by middleware
# Example in an endpoint:
"""
from app.core.logging import logger

@router.post("/example")
async def example_endpoint():
    logger.info("Processing example request")
    # The log will automatically include the request_id from middleware
    return {"status": "ok"}
"""
