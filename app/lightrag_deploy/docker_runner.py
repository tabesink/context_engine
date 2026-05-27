import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class DockerComposeRunner(Protocol):
    def up(self, service_name: str) -> CommandResult: ...

    def stop(self, service_name: str) -> CommandResult: ...

    def recreate(self, service_name: str) -> CommandResult: ...

    def ps(self) -> CommandResult: ...


class SubprocessDockerComposeRunner:
    def __init__(self, *, compose_file: Path, compose_bin: str, timeout_seconds: int):
        self.compose_file = compose_file
        self.compose_bin = compose_bin
        self.timeout_seconds = timeout_seconds

    def up(self, service_name: str) -> CommandResult:
        return self._run(["up", "-d", service_name])

    def stop(self, service_name: str) -> CommandResult:
        return self._run(["stop", service_name])

    def recreate(self, service_name: str) -> CommandResult:
        return self._run(["up", "-d", "--force-recreate", service_name])

    def ps(self) -> CommandResult:
        return self._run(["ps"])

    def _run(self, args: list[str]) -> CommandResult:
        command = [*shlex.split(self.compose_bin), "-f", str(self.compose_file), *args]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            missing = shlex.split(self.compose_bin)[0] if self.compose_bin else "docker"
            return CommandResult(
                exit_code=127,
                stdout="",
                stderr=f"Missing runtime dependency '{missing}': {exc}",
            )
        except subprocess.TimeoutExpired as exc:
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            return CommandResult(
                exit_code=124,
                stdout=stdout,
                stderr=stderr or f"Command timed out after {self.timeout_seconds}s",
            )
        return CommandResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
