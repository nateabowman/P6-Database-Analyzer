"""Prometheus metrics exporter for P6 Database Analyzer."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from utils.logging_config import get_logger
from utils.metrics import get_metrics

logger = get_logger(__name__)

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

analysis_requests_total = Counter(
    'analysis_requests_total',
    'Total analysis requests',
    ['analysis_type', 'status']
)

analysis_duration_seconds = Histogram(
    'analysis_duration_seconds',
    'Analysis duration in seconds',
    ['analysis_type']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections',
    ['db_type']
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['db_type', 'status']
)


class PrometheusMetricsExporter:
    """Exports metrics to Prometheus format."""
    
    def __init__(self):
        self.metrics = get_metrics()
    
    def export_metrics(self) -> Response:
        """
        Export metrics in Prometheus format.
        
        Returns:
            FastAPI Response with metrics
        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_analysis(self, analysis_type: str, status: str, duration: float):
        """Record analysis metrics."""
        analysis_requests_total.labels(analysis_type=analysis_type, status=status).inc()
        analysis_duration_seconds.labels(analysis_type=analysis_type).observe(duration)
    
    def update_connection_gauge(self, db_type: str, count: int):
        """Update database connection gauge."""
        database_connections_active.labels(db_type=db_type).set(count)
    
    def record_database_query(self, db_type: str, status: str):
        """Record database query metrics."""
        database_queries_total.labels(db_type=db_type, status=status).inc()


# Global exporter instance
_exporter: PrometheusMetricsExporter = None


def get_metrics_exporter() -> PrometheusMetricsExporter:
    """Get the global metrics exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = PrometheusMetricsExporter()
    return _exporter

