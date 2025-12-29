"""OpenTelemetry tracing for distributed tracing."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from typing import Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(service_name: str = "p6-analyzer", endpoint: Optional[str] = None):
    """
    Set up OpenTelemetry tracing.
    
    Args:
        service_name: Service name for tracing
        endpoint: OTLP endpoint (optional, uses console exporter if None)
    """
    global _tracer_provider
    
    try:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        
        if endpoint:
            # Use OTLP exporter for production
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint)
        else:
            # Use console exporter for development
            exporter = ConsoleSpanExporter()
        
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        
        _tracer_provider = provider
        
        logger.info(f"Tracing initialized for service: {service_name}")
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {str(e)}")


def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def instrument_fastapi(app):
    """Instrument FastAPI application for tracing."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {str(e)}")


def instrument_requests():
    """Instrument requests library for tracing."""
    try:
        RequestsInstrumentor().instrument()
        logger.info("Requests library instrumented for tracing")
    except Exception as e:
        logger.warning(f"Failed to instrument requests: {str(e)}")

