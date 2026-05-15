# CLI ASCII Render Conformance

The human CLI output contract is documented in
`docs/cli_docs/04_ragcli_api_surface_ascii_example/ragcli_ascii_api_surface_examples.md`.
The conformance tests treat that document as the visual spec for screen titles,
ASCII-only tables, actionable `Next:` commands, and planned backend-gap wording.

## Test Workflow

Run the focused conformance suite while changing CLI screens:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

Then run the existing CLI/TUI coverage:

```bash
pytest tests/test_cli_screen_renderers.py tests/test_cli_tui.py tests/test_cli.py -q
```

The sample tests intentionally exercise public command paths through Typer or
the shared renderer. They should not assert private builder internals unless the
builder output is itself the public contract for a screen.

## Adding A Sample

1. Add or update the `Command:` block and following `Example human output:` text
   block in the ASCII examples document.
2. Add the command to `tests/test_cli_ascii_samples.py` if it is implemented or
   intentionally reserved as a backend gap.
3. Keep JSON behavior covered separately. Human-only titles, tables, and
   `Next:` hints must not appear in `--output json`.

## Manual Docs Upload

Docs are not uploaded automatically by the build. After logging in to the target
backend, upload the relevant CLI docs explicitly:

```bash
ragcli admin documents upload --file docs/cli_docs/04_ragcli_api_surface_ascii_example/ragcli_ascii_api_surface_examples.md
ragcli admin documents upload --file docs/cli_docs/ascii_render_conformance.md
```

Set `--api-base-url` first, or log in against the desired backend before running
the upload commands. Check ingestion with:

```bash
ragcli jobs list
ragcli documents list
```
