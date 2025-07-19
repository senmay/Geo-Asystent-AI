"""Monitoring and metrics middleware for FastAPI."""

import time
import logging
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple in-memory metrics collector."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=max_history)
        self.status_codes = defaultdict(int)
        self.endpoints = defaultdict(int)
        self.errors_by_type = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_request(self, method: str, path: str, status_code: int, response_time: float, error_type: str = None):
        """Record a request with its metrics."""
        self.request_count += 1
        self.response_times.append(response_time)
        self.status_codes[status_code] += 1
        self.endpoints[f"{method} {path}"] += 1
        
        if status_code >= 400:
            self.error_count += 1
            if error_type:
                self.errors_by_type[error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        uptime = datetime.now() - self.start_time
        
        # Calculate response time statistics
        response_times_list = list(self.response_times)
        avg_response_time = sum(response_times_list) / len(response_times_list) if response_times_list else 0
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            "average_response_time": round(avg_response_time, 3),
            "status_codes": dict(self.status_codes),
            "top_endpoints": dict(sorted(self.endpoints.items(), key=lambda x: x[1], reverse=True)[:10]),
            "errors_by_type": dict(self.errors_by_type),
            "recent_response_times": response_times_list[-10:] if response_times_list else []
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting application metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        error_type = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            error_type = type(e).__name__
            # Re-raise the exception to be handled by error handlers
            raise
        finally:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                response_time=response_time,
                error_type=error_type
            )
            
            # Log slow requests
            if response_time > 5.0:  # Log requests taking more than 5 seconds
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} - {response_time:.3f}s",
                    extra={
                        "slow_request": True,
                        "method": request.method,
                        "path": request.url.path,
                        "response_time": response_time,
                        "status_code": status_code
                    }
                )
        
        return response


def setup_monitoring_middleware(app: FastAPI) -> None:
    """Set up monitoring middleware for the FastAPI application."""
    app.add_middleware(MonitoringMiddleware)
    
    # Add metrics endpoint
    @app.get("/api/v1/metrics")
    async def get_metrics():
        """Get application metrics."""
        return metrics_collector.get_metrics()
    
    # Add health check endpoint
    @app.get("/api/v1/health")
    async def health_check():
        """Health check endpoint."""
        metrics = metrics_collector.get_metrics()
        
        # Determine health status based on error rate and response time
        is_healthy = (
            metrics["error_rate"] < 50 and  # Less than 50% error rate
            metrics["average_response_time"] < 10  # Average response time under 10 seconds
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": metrics["uptime_seconds"],
            "total_requests": metrics["total_requests"],
            "error_rate": metrics["error_rate"],
            "average_response_time": metrics["average_response_time"]
        }
    
    logger.info("Monitoring middleware and endpoints set up successfully")