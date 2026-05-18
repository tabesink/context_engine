from pathlib import Path

from cli import launcher
from cli.config import CliSettings


def test_launcher_uses_loaded_settings(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_load_settings(_argv=None) -> CliSettings:
        return CliSettings(
            api_base_url="http://127.0.0.1:8999",
            config_dir=tmp_path,
            keyring_enabled=False,
        )

    def fake_run_tui(*, api_base_url, credential_store, client_factory, console) -> None:  # noqa: ANN001
        captured["api_base_url"] = api_base_url
        captured["config_dir"] = credential_store.config_dir
        captured["keyring_enabled"] = credential_store._keyring is not None
        captured["client_factory"] = client_factory
        captured["console_width"] = console.width

    monkeypatch.setattr("cli.launcher.load_cli_settings", fake_load_settings)
    monkeypatch.setattr("cli.launcher.run_tui", fake_run_tui)

    launcher.main()

    assert captured["api_base_url"] == "http://127.0.0.1:8999"
    assert captured["config_dir"] == tmp_path
    assert captured["keyring_enabled"] is False
    assert captured["client_factory"].__name__ == "ApiClient"
    assert int(captured["console_width"]) >= 80


def test_launcher_exits_cleanly_on_keyboard_interrupt(monkeypatch) -> None:
    monkeypatch.setattr(
        "cli.launcher.load_cli_settings",
        lambda _argv=None: CliSettings(
            api_base_url="http://127.0.0.1:8000",
            config_dir=Path("irrelevant"),
            keyring_enabled=False,
        ),
    )

    def raise_interrupt(**kwargs):  # noqa: ANN003, ANN201
        raise KeyboardInterrupt()

    monkeypatch.setattr("cli.launcher.run_tui", raise_interrupt)

    launcher.main()
