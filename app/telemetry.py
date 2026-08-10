"""
OpenTelemetry wiring. Every pipeline stage gets its own span so latency
regressions can be attributed to a stage instead of guessed at.

If OTEL_EXPORTER_OTLP_ENDPOINT is unset, spans are exported to console —
good enough to see the shape of a trace locally without standing up a
collector.
"""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from app.config import settings

_resource = Resource.create({"service.name": "rag-pipeline"})
_provider = TracerProvider(resource=_resource)

if settings.otel_exporter_otlp_endpoint:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )

    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
else:
    exporter = ConsoleSpanExporter()

_provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(_provider)

tracer = trace.get_tracer("rag_pipeline")
