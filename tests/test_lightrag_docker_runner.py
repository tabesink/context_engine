import subprocess
from pathlib import Path

from app.lightrag_deploy.docker_runner import SubprocessDockerComposeRunner


def test_runner_returns_failed_result_when_compose_binary_missing(
    monkeypatch,
) -> None:
    def fake_run(*args, **kwargs):  # pragma: no cover - deterministic branch
        del args, kwargs
        raise FileNotFoundError("[Errno 2] No such file or directory: 'docker'")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = SubprocessDockerComposeRunner(
        compose_file=Path("/tmp/compose.yml"),
        compose_bin="docker compose",
        timeout_seconds=30,
    )

    result = runner.stop("lightrag_test")

    assert result.exit_code == 127
    assert "Missing runtime dependency 'docker'" in result.stderr


def test_runner_returns_timeout_result_when_compose_command_times_out(
    monkeypatch,
) -> None:
    def fake_run(*args, **kwargs):  # pragma: no cover - deterministic branch
        del args
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", "docker compose"), timeout=30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = SubprocessDockerComposeRunner(
        compose_file=Path("/tmp/compose.yml"),
        compose_bin="docker compose",
        timeout_seconds=30,
    )

    result = runner.ps()

    assert result.exit_code == 124
    assert result.stderr == "Command timed out after 30s"
