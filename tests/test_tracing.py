import pytest
from core.logging import add_trace_id
from core.tracing import instrument, setup_tracing
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)


@pytest.fixture
def traced():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    seen = {}
    app = FastAPI()

    @app.get("/api/v1/projects/{slug}")
    def project(slug: str):
        record = {"extra": {}}
        add_trace_id(record)
        seen["log"] = record["extra"]["trace"]
        return {"slug": slug}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    instrument(app, provider)
    yield TestClient(app), exporter, seen
    # Both patch their libraries globally; leave other tests untraced.
    RedisInstrumentor().uninstrument()
    HTTPXClientInstrumentor().uninstrument()


def test_a_request_becomes_a_trace_named_after_its_route(traced):
    client, exporter, _ = traced

    client.get("/api/v1/projects/papit")

    server = [s for s in exporter.get_finished_spans() if s.kind.name == "SERVER"]
    assert [s.name for s in server] == ["GET /api/v1/projects/{slug}"]
    assert server[0].attributes["http.route"] == "/api/v1/projects/{slug}"


def test_logs_inside_a_request_carry_its_trace_id(traced):
    client, exporter, seen = traced

    client.get("/api/v1/projects/papit")

    trace_id = exporter.get_finished_spans()[0].context.trace_id
    assert seen["log"] == f" trace_id={trace_id:032x}"


def test_logs_outside_a_request_have_no_trace_id():
    record = {"extra": {}}

    add_trace_id(record)

    assert record["extra"]["trace"] == ""


def test_health_probes_are_not_traced(traced):
    client, exporter, _ = traced

    client.get("/health")

    assert exporter.get_finished_spans() == ()


def test_tracing_is_off_without_an_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    assert setup_tracing(FastAPI(), engine=None) is False
