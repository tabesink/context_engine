from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.lightrag_deploy.compose import ComposeGenerator, write_domain_env
from app.lightrag_deploy.manifest import DomainManifestStore
from app.lightrag_deploy.models import DomainLLMSnapshot, LightRAGDomain
from app.lightrag_deploy.paths import DomainPathResolver
from app.lightrag_deploy.settings import LightRAGDeploySettings


def _settings(tmp_path: Path) -> LightRAGDeploySettings:
    return LightRAGDeploySettings(
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.lightrag-domains.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
        dockerfile=Path("docker/lightrag.Dockerfile"),
        build_context=Path("."),
    )


def _settings_with_provider(tmp_path: Path) -> LightRAGDeploySettings:
    return replace(
        _settings(tmp_path),
        llm_binding="openai",
        llm_binding_host="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1",
        llm_binding_api_key="test-bedrock-key",
        llm_model="openai.gpt-oss-20b-1:0",
        embedding_binding="openai",
        embedding_binding_host="https://api.openai.com/v1",
        embedding_binding_api_key="test-openai-key",
        embedding_model="text-embedding-3-large",
        embedding_dim=3072,
        embedding_token_limit=8192,
        embedding_send_dim=False,
        embedding_use_base64=True,
        openai_llm_max_tokens=9000,
    )


def _domain(tmp_path: Path, domain_id: str = "fatigue", port: int = 9622) -> LightRAGDomain:
    settings = _settings(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths(domain_id)
    timestamp = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    return LightRAGDomain(
        id=domain_id,
        display_name="Fatigue Manuals",
        postgres_database=f"lightrag_{domain_id.replace('-', '_')}",
        postgres_user=f"lightrag_{domain_id.replace('-', '_')}",
        host="127.0.0.1",
        host_port=port,
        container_port=9621,
        base_url=f"http://127.0.0.1:{port}",
        host_base_url=f"http://127.0.0.1:{port}",
        container_base_url=f"http://lightrag_{domain_id}:9621",
        container_name=f"context_engine_lightrag_{domain_id}",
        service_name=f"lightrag_{domain_id}",
        status="configured",
        paths=paths.as_manifest_paths(),
        is_default=True,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_missing_manifest_returns_empty_domain_list(tmp_path: Path) -> None:
    store = DomainManifestStore(_settings(tmp_path).manifest_path)

    assert store.list_domains() == []


def test_manifest_writes_deterministic_domain_list(tmp_path: Path) -> None:
    store = DomainManifestStore(_settings(tmp_path).manifest_path)
    domain = _domain(tmp_path)

    store.add_domain(domain)

    assert store.list_domains() == [domain]
    assert _settings(tmp_path).manifest_path.read_text(encoding="utf-8") == (
        '{\n'
        '  "domains": [\n'
        "    {\n"
        '      "base_url": "http://127.0.0.1:9622",\n'
        '      "container_base_url": "http://lightrag_fatigue:9621",\n'
        '      "container_name": "context_engine_lightrag_fatigue",\n'
        '      "container_port": 9621,\n'
        '      "created_at": "2026-05-18T14:30:00Z",\n'
        '      "display_name": "Fatigue Manuals",\n'
        '      "host": "127.0.0.1",\n'
        '      "host_base_url": "http://127.0.0.1:9622",\n'
        '      "host_port": 9622,\n'
        '      "id": "fatigue",\n'
        '      "is_default": true,\n'
        '      "paths": {\n'
        f'        "artifacts": "{(tmp_path / "lightrag/domains/fatigue/artifacts").as_posix()}",\n'
        f'        "env_file": "{(tmp_path / "lightrag/domains/fatigue/domain.env").as_posix()}",\n'
        f'        "inputs": "{(tmp_path / "lightrag/domains/fatigue/inputs").as_posix()}",\n'
        f'        "logs": "{(tmp_path / "lightrag/domains/fatigue/logs").as_posix()}",\n'
        f'        "rag_storage": "{(tmp_path / "lightrag/domains/fatigue/rag_storage").as_posix()}",\n'
        f'        "root": "{(tmp_path / "lightrag/domains/fatigue").as_posix()}"\n'
        "      },\n"
        '      "postgres_database": "lightrag_fatigue",\n'
        '      "postgres_user": "lightrag_fatigue",\n'
        '      "retrieval_defaults": {\n'
        '        "chunk_rerank_top_k": 10,\n'
        '        "chunk_top_k": 10,\n'
        '        "max_token_for_global_context": 4000,\n'
        '        "max_token_for_local_context": 4000,\n'
        '        "max_token_for_text_unit": 4000,\n'
        '        "top_k": 10\n'
        "      },\n"
        '      "service_name": "lightrag_fatigue",\n'
        '      "status": "configured",\n'
        '      "updated_at": "2026-05-18T14:30:00Z"\n'
        "    }\n"
        "  ],\n"
        '  "version": 1\n'
        "}\n"
    )


def test_manifest_rejects_duplicate_domain_id_and_port(tmp_path: Path) -> None:
    store = DomainManifestStore(_settings(tmp_path).manifest_path)
    store.add_domain(_domain(tmp_path, "fatigue", 9622))

    with pytest.raises(ValueError, match="already exists"):
        store.add_domain(_domain(tmp_path, "fatigue", 9623))
    with pytest.raises(ValueError, match="port"):
        store.add_domain(_domain(tmp_path, "abaqus", 9622))


def test_domain_env_uses_per_domain_postgres_credentials_by_default(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)

    assert paths.env_file.read_text(encoding="utf-8") == (
        "# Generated by Context Engine. Do not edit by hand.\n"
        "# Source of truth: root .env + .data/lightrag/domains.json\n"
        "# Domain: fatigue\n"
        "\n"
        "WORKSPACE=fatigue\n"
        "HOST=0.0.0.0\n"
        "PORT=9621\n"
        "INPUT_DIR=/app/data/inputs\n"
        "WORKING_DIR=/app/data/rag_storage\n"
        "LOG_DIR=/app/data/logs\n"
        "TOP_K=10\n"
        "CHUNK_TOP_K=10\n"
        "CHUNK_RERANK_TOP_K=10\n"
        "MAX_TOKEN_TEXT_CHUNK=4000\n"
        "MAX_TOKEN_RELATION_DESC=4000\n"
        "MAX_TOKEN_ENTITY_DESC=4000\n"
        "LIGHTRAG_KV_STORAGE=PGKVStorage\n"
        "LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage\n"
        "LIGHTRAG_GRAPH_STORAGE=PGGraphStorage\n"
        "LIGHTRAG_VECTOR_STORAGE=PGVectorStorage\n"
        "POSTGRES_HOST=postgres\n"
        "POSTGRES_PORT=5432\n"
        "POSTGRES_DATABASE=lightrag_fatigue\n"
        "POSTGRES_USER=lightrag_fatigue\n"
        "POSTGRES_PASSWORD=lightrag\n"
        "POSTGRES_VECTOR_INDEX_TYPE=HNSW\n"
        "TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken\n"
        "\n"
        "# Model provider configuration\n"
        "LLM_BINDING=openai\n"
        "\n"
        "# Embedding provider configuration\n"
        "EMBEDDING_BINDING=openai\n"
        "\n"
        "# OpenAI-compatible provider tuning\n"
    )


def test_domain_env_does_not_use_app_runtime_postgres_credentials(tmp_path: Path) -> None:
    settings = replace(
        _settings(tmp_path),
        runtime_postgres_database="context_engine",
        runtime_postgres_user="context_engine",
        runtime_postgres_password="context_engine",
    )
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "POSTGRES_DATABASE=context_engine" not in env_text
    assert "POSTGRES_USER=context_engine" not in env_text
    assert "POSTGRES_PASSWORD=context_engine" not in env_text


def test_domain_env_includes_bedrock_openai_compatible_provider_config(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "LLM_BINDING=openai" in env_text
    assert "LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1" in env_text
    assert "LLM_BINDING_API_KEY=test-bedrock-key" in env_text
    assert "LLM_MODEL=openai.gpt-oss-20b-1:0" in env_text
    assert "EMBEDDING_BINDING=openai" in env_text
    assert "EMBEDDING_BINDING_HOST=https://api.openai.com/v1" in env_text
    assert "EMBEDDING_BINDING_API_KEY=test-openai-key" in env_text
    assert "EMBEDDING_MODEL=text-embedding-3-large" in env_text
    assert "EMBEDDING_DIM=3072" in env_text
    assert "EMBEDDING_TOKEN_LIMIT=8192" in env_text
    assert "EMBEDDING_SEND_DIM=false" in env_text
    assert "EMBEDDING_USE_BASE64=true" in env_text
    assert "OPENAI_LLM_MAX_TOKENS=9000" in env_text


def test_domain_env_can_prefer_resolved_llm_profile_over_shell_settings(tmp_path: Path) -> None:
    settings = replace(
        _settings_with_provider(tmp_path),
        llm_binding_host="http://stale-provider.local/v1",
        llm_binding_api_key="stale-runtime-key",
        llm_model="mistral-nemo:latest",
    )
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)
    llm = DomainLLMSnapshot(
        profile_id="bedrock-gpt-oss-120b",
        provider="bedrock_openai",
        binding="openai",
        base_url="https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1",
        api_key_env_var="AWS_BEARER_TOKEN_BEDROCK",
        model="openai.gpt-oss-120b-1:0",
    )

    write_domain_env(
        domain,
        settings,
        paths,
        provider_secrets={"AWS_BEARER_TOKEN_BEDROCK": "stored-bedrock-key"},
        llm=llm,
    )
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "LLM_BINDING=openai" in env_text
    assert "LLM_BINDING_HOST=https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1" in env_text
    assert "LLM_BINDING_API_KEY=stored-bedrock-key" in env_text
    assert "LLM_MODEL=openai.gpt-oss-120b-1:0" in env_text
    assert "mistral-nemo:latest" not in env_text
    assert "stale-runtime-key" not in env_text


def test_domain_env_skips_blank_optional_provider_values(tmp_path: Path) -> None:
    settings = replace(
        _settings_with_provider(tmp_path),
        keyword_llm_model="",
        query_llm_model=" ",
        vlm_llm_model=None,
        openai_llm_max_completion_tokens=None,
        openai_llm_temperature=None,
        openai_llm_extra_body="",
    )
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "KEYWORD_LLM_MODEL=" not in env_text
    assert "QUERY_LLM_MODEL=" not in env_text
    assert "VLM_LLM_MODEL=" not in env_text
    assert "OPENAI_LLM_MAX_COMPLETION_TOKENS=" not in env_text
    assert "OPENAI_LLM_TEMPERATURE=" not in env_text
    assert "OPENAI_LLM_EXTRA_BODY=" not in env_text


def test_provider_boolean_flags_are_lowercase_in_domain_env(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "EMBEDDING_SEND_DIM=false" in env_text
    assert "EMBEDDING_USE_BASE64=true" in env_text


def test_provider_secrets_are_not_written_to_manifest_or_compose(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    domain = _domain(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    store = DomainManifestStore(settings.manifest_path)

    write_domain_env(domain, settings, paths)
    store.add_domain(domain)
    compose_output = ComposeGenerator(settings).render([domain])
    manifest_text = settings.manifest_path.read_text(encoding="utf-8")
    env_text = paths.env_file.read_text(encoding="utf-8")

    assert "test-bedrock-key" in env_text
    assert "test-openai-key" in env_text
    assert "test-bedrock-key" not in compose_output
    assert "test-openai-key" not in compose_output
    assert "test-bedrock-key" not in manifest_text
    assert "test-openai-key" not in manifest_text


def test_compose_generation_is_deterministic(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    domain = _domain(tmp_path)

    output = ComposeGenerator(settings).render([domain])
    root = Path.cwd().resolve().as_posix()

    assert "# Generated by Context Engine. Do not edit by hand." in output
    assert "lightrag_fatigue:" in output
    assert "build:" in output
    assert f"context: {root}" in output
    assert f"dockerfile: {root}/docker/lightrag.Dockerfile" in output
    assert "image: " not in output
    assert f"- {domain.paths['env_file']}:/app/domain.env:ro" not in output
    assert f"- {domain.paths['env_file']}" in output
    assert '- "127.0.0.1:9622:9621"' in output
    assert f"- {domain.paths['inputs']}:/app/data/inputs" in output
    assert "    networks:\n      context_engine_lightrag:\n        aliases:\n          - lightrag_fatigue" in output
    assert "    external: true" in output
    assert f"name: {settings.docker_network}" in output


def test_compose_generation_can_build_lightrag_from_local_source(tmp_path: Path) -> None:
    settings = LightRAGDeploySettings(
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.lightrag-domains.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
        dockerfile=Path("docker/lightrag.Dockerfile"),
        build_context=Path("."),
    )
    domain = _domain(tmp_path)

    output = ComposeGenerator(settings).render([domain])
    root = Path.cwd().resolve().as_posix()

    assert "build:" in output
    assert f"context: {root}" in output
    assert f"dockerfile: {root}/docker/lightrag.Dockerfile" in output
    assert "image: " not in output


def test_compose_generation_resolves_relative_domain_paths_for_env_and_volumes() -> None:
    settings = LightRAGDeploySettings(
        deploy_root=Path(".data/lightrag"),
        domains_root=Path(".data/lightrag/domains"),
        manifest_path=Path(".data/lightrag/domains.json"),
        compose_file=Path(".data/lightrag/docker-compose.lightrag-domains.yml"),
        deleted_root=Path(".data/lightrag/deleted"),
    )
    timestamp = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    domain = LightRAGDomain(
        id="smokegraph",
        display_name="Smoke Graph",
        host="127.0.0.1",
        host_port=9622,
        container_port=9621,
        base_url="http://127.0.0.1:9622",
        host_base_url="http://127.0.0.1:9622",
        container_base_url="http://lightrag_smokegraph:9621",
        container_name="context_engine_lightrag_smokegraph",
        service_name="lightrag_smokegraph",
        status="configured",
        paths={
            "root": ".data/lightrag/domains/smokegraph",
            "env_file": ".data/lightrag/domains/smokegraph/domain.env",
            "inputs": ".data/lightrag/domains/smokegraph/inputs",
            "rag_storage": ".data/lightrag/domains/smokegraph/rag_storage",
            "artifacts": ".data/lightrag/domains/smokegraph/artifacts",
            "logs": ".data/lightrag/domains/smokegraph/logs",
        },
        is_default=True,
        created_at=timestamp,
        updated_at=timestamp,
    )

    output = ComposeGenerator(settings).render([domain])
    root = Path.cwd().resolve().as_posix()

    assert f"- {root}/.data/lightrag/domains/smokegraph/domain.env" in output
    assert f"- {root}/.data/lightrag/domains/smokegraph/inputs:/app/data/inputs" in output
