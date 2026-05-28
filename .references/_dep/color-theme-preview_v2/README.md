# Graphite Accent Theme Preview

Standalone browser preview for Context Engine accent palette options. Compare five Graphite + accent themes in realistic UI examples without touching the main app.

## Open the preview

```bash
# Option A: open directly
xdg-open .references/color-theme-preview/index.html

# Option B: local server (uv — avoids pulling repo deps)
cd .references/color-theme-preview
uv run --no-config -m http.server 8765
# then visit http://localhost:8765

# If port 8765 is in use, pick another:
uv run --no-config -m http.server 8766
```

Use `--no-config` so uv does not sync the parent Context Engine project (which would download heavy ML/CUDA packages just to serve a static HTML file).

## What's included

- **Muted Teal** (recommended default)
- Soft Indigo
- Sage Green
- Warm Amber
- Steel Blue

Each theme shows accent tokens applied to settings nav, provider selection, domain pills, evidence/citations, workspace tree, status badges, and upload progress — with semantic colors (success/warning/danger/info) shown separately.

## Notes

- Preview-only artifact; not wired into the app theme system.
- Light mode only. No build step or external dependencies.
