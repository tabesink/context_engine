# Registry runtime URL patch

In `app/services/lightrag_domain_registry.py`, change `get_required()`.

Current behavior uses persisted `base_url`.

Target:

```python
def _runtime_base_url(self, entry: dict[str, Any], requested: str) -> str:
    mode = (self.settings.lightrag_docker_execution_mode or "host").lower()
    if mode == "socket":
        value = entry.get("container_base_url")
    else:
        value = entry.get("host_base_url")
    base_url = str(value or entry.get("base_url") or "").strip().rstrip("/")
    if not base_url:
        raise LightRAGDomainRegistryInvalidError(
            f"LightRAG domain '{requested}' does not define a runtime URL"
        )
    return base_url
```

Then in `get_required()`:

```python
base_url = self._runtime_base_url(entry, requested)
```
