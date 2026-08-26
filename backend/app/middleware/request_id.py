"""
Request ID Middleware
Adds unique request IDs for tracing
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from loguru import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        logger.debug(f"Request {request_id}: {request.method} {request.url.path}")
        return response
