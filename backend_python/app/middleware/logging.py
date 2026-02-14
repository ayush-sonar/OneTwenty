import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging import logger, set_request_id
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses.
    Automatically generates and tracks request_id for correlation.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        req_id = str(uuid.uuid4())
        set_request_id(req_id)
        
        # Start timer
        start_time = time.time()
        
        # Read request body (for POST/PUT/PATCH)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = body_bytes.decode('utf-8')
                    # Try to parse as JSON for better logging
                    try:
                        request_body = json.loads(request_body)
                    except:
                        pass
            except:
                request_body = "<unable to read body>"
        
        # Log incoming request
        logger.info(
            "Incoming request",
            extra={
                'extra_data': {
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': dict(request.query_params),
                    'body': request_body,
                    'client_host': request.client.host if request.client else None,
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            logger.error(
                f"Request failed with exception: {str(e)}",
                exc_info=True,
                extra={
                    'extra_data': {
                        'method': request.method,
                        'path': request.url.path,
                    }
                }
            )
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log outgoing response
        logger.info(
            "Outgoing response",
            extra={
                'extra_data': {
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                }
            }
        )
        
        # Add request ID to response headers for client-side debugging
        response.headers['X-Request-ID'] = req_id
        
        return response
