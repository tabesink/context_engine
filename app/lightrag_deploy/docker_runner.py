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
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        return CommandResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
