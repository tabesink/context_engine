import os
import socket
from pathlib import Path

import httpx

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["ENVIRONMENT"] = "test"
Path(".data").mkdir(parents=True, exist_ok=True)

from app.core.config import Settings  # noqa: E402
from app.services.lightrag_reachability_service import LightRAGReachabilityService  # noqa: E402
from app.storage.db import create_db_and_tables  # noqa: E402


def setup_function() -> None:
    create_db_and_tables()


def _settings(tmp_path, *, execution_mode: str = "socket") -> Settings:
    manifest = tmp_path / "domains.json"
    manifest.write_text(
        (
            '{"domains":['
            '{"id":"fatigue","display_name":"Fatigue","base_url":"http://127.0.0.1:9621",'
            '"host_base_url":"http://127.0.0.1:9621",'
            '"container_base_url":"http://lightrag_fatigue:9621",'
            '"api_key":"domain-key","status":"running","is_default":true}'
            "]}"
        ),
        encoding="utf-8",
    )
    return Settings(
        environment="test",
        lightrag_domain_registry=manifest,
        lightrag_docker_execution_mode=execution_mode,
    )


def test_lightrag_reachability_uses_resolved_container_url_in_socket_mode(tmp_path) -> None:
    seen = {}

    def fake_get(url, **kwargs):
        seen["url"] = url
        seen["headers"] = kwargs.get("headers")
        return httpx.Response(200)

    report = LightRAGReachabilityService(
        settings=_settings(tmp_path),
        http_get=fake_get,
        dns_lookup=lambda host: [(host,)],
    ).probe("fatigue")

    assert report.healthy is True
    assert report.domain_id == "fatigue"
    assert report.base_url == "http://lightrag_fatigue:9621"
    assert seen["url"] == "http://lightrag_fatigue:9621/health"
    assert seen["headers"] == {"X-API-Key": "domain-key"}


def test_lightrag_reachability_reports_dns_failure_as_unreachable(tmp_path) -> None:
    def fake_get(url, **kwargs):
        del url, kwargs
        raise AssertionError("HTTP should not be attempted after DNS failure")

    def fake_dns(host):
        del host
        raise socket.gaierror("[Errno -3] Temporary failure in name resolution")

    report = LightRAGReachabilityService(
        settings=_settings(tmp_path),
        http_get=fake_get,
        dns_lookup=fake_dns,
    ).probe("fatigue")

    assert report.healthy is False
    assert report.code == "lightrag_domain_unreachable"
    assert report.reason_code == "dns_failed"
    assert "Temporary failure in name resolution" in (report.reason or "")


def test_lightrag_reachability_reports_connection_refused(tmp_path) -> None:
    def fake_get(url, **kwargs):
        del url, kwargs
        raise httpx.ConnectError("[Errno 111] Connection refused")

    report = LightRAGReachabilityService(
        settings=_settings(tmp_path),
        http_get=fake_get,
        dns_lookup=lambda host: [(host,)],
    ).probe("fatigue")

    assert report.healthy is False
    assert report.code == "lightrag_domain_unreachable"
    assert report.reason_code == "connection_refused"


def test_lightrag_reachability_reports_timeout(tmp_path) -> None:
    def fake_get(url, **kwargs):
        del url, kwargs
        raise httpx.TimeoutException("slow")

    report = LightRAGReachabilityService(
        settings=_settings(tmp_path),
        http_get=fake_get,
        dns_lookup=lambda host: [(host,)],
    ).probe("fatigue")

    assert report.healthy is False
    assert report.code == "lightrag_domain_unreachable"
    assert report.reason_code == "timeout"


def test_lightrag_reachability_reports_unhealthy_health_status(tmp_path) -> None:
    def fake_get(url, **kwargs):
        del url, kwargs
        return httpx.Response(503)

    report = LightRAGReachabilityService(
        settings=_settings(tmp_path),
        http_get=fake_get,
        dns_lookup=lambda host: [(host,)],
    ).probe("fatigue")

    assert report.healthy is False
    assert report.code == "lightrag_domain_unhealthy"
    assert report.reason_code == "bad_response"
    assert report.status_code == 503
