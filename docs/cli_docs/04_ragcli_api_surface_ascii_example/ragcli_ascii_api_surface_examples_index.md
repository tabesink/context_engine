# ragcli ASCII examples — short index

Companion to [`ragcli_ascii_api_surface_examples.md`](ragcli_ascii_api_surface_examples.md): full ASCII samples, commands, and implementation notes for every `ragcli` human-mode surface.

**How to use:** Find the command or topic below. **Detail** links jump to the matching heading in the full doc (GitHub-style `#L` line anchors).

---

## 1. Session / auth

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 1.1 | `ragcli login --email …` | Successful login table, failed login, token security note | [L19](ragcli_ascii_api_surface_examples.md#L19) |
| 1.2 | `ragcli auth me` | Current user/session table; not-logged-in gate | [L75](ragcli_ascii_api_surface_examples.md#L75) |
| 1.3 | `ragcli logout` | Local session cleared; what was wiped | [L118](ragcli_ascii_api_surface_examples.md#L118) |

---

## 2. Documents and retrieval

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 2.1 | `ragcli documents list` | Document index table; empty state | [L151](ragcli_ascii_api_surface_examples.md#L151) |
| 2.2 | `ragcli documents show --document-id …` | Single document metadata | [L193](ragcli_ascii_api_surface_examples.md#L193) |
| 2.3 | `ragcli documents structure --document-id …` | Outline / section–page map | [L236](ragcli_ascii_api_surface_examples.md#L236) |
| 2.4 | `ragcli documents page --document-id … --page-number …` | One page body + context | [L271](ragcli_ascii_api_surface_examples.md#L271) |
| 2.5 | `ragcli documents retrieve --query …` | Full retrieval: request summary, ranked results, evidence blocks, “Next” | [L306](ragcli_ascii_api_surface_examples.md#L306) |
| 2.6 | `ragcli documents retrieve … --include-debug` | Same as 2.5 plus admin-only **Debug** panel | [L394](ragcli_ascii_api_surface_examples.md#L394) |
| 2.7 | `ragcli documents answer --query …` | Composed answer + cited sources table | [L445](ragcli_ascii_api_surface_examples.md#L445) |
| 2.8 | `ragcli query --query …` | Top-level Q&A (corpus-wide) | [L484](ragcli_ascii_api_surface_examples.md#L484) |
| 2.9 | `ragcli documents content --pages …` | **Backend gap** → `not_supported_by_backend`; suggests `GET /documents/{id}/content?pages=` | [L519](ragcli_ascii_api_surface_examples.md#L519) |
| 2.10 | `ragcli documents search --query …` | **Backend gap**; suggests `GET /documents/search?q=` | [L549](ragcli_ascii_api_surface_examples.md#L549) |

---

## 3. LightRAG graph

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 3.1 | `ragcli lightrag labels list` | Label catalog table | [L581](ragcli_ascii_api_surface_examples.md#L581) |
| 3.2 | `ragcli lightrag labels popular --limit …` | Labels with usage counts | [L611](ragcli_ascii_api_surface_examples.md#L611) |
| 3.3 | `ragcli lightrag labels search --query …` | Fuzzy / scored label search | [L640](ragcli_ascii_api_surface_examples.md#L640) |
| 3.4 | `ragcli lightrag graphs show --label …` | Graph summary, top related labels; JSON note for viz | [L672](ragcli_ascii_api_surface_examples.md#L672) |
| 3.5 | `ragcli lightrag labels popular` (etc.) | **LightRAG disabled** service error and remediation | [L724](ragcli_ascii_api_surface_examples.md#L724) |

---

## 4. Admin documents

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 4.1 | `ragcli admin documents upload --file …` | Upload → local job path vs LightRAG-forwarded path | [L751](ragcli_ascii_api_surface_examples.md#L751) |
| 4.2 | `ragcli admin documents list` | Admin listing with index backend column | [L808](ragcli_ascii_api_surface_examples.md#L808) |
| 4.3 | `ragcli admin documents index --document-id …` | Index job accepted + job id | [L837](ragcli_ascii_api_surface_examples.md#L837) |
| 4.4 | `ragcli admin documents reindex --document-id …` | Reindex job accepted | [L872](ragcli_ascii_api_surface_examples.md#L872) |
| 4.5 | `ragcli admin documents delete --document-id …` | Hard delete confirmation block | [L907](ragcli_ascii_api_surface_examples.md#L907) |
| 4.6 | `ragcli admin documents list` (as non-admin) | **403 forbidden**; no client-side admin guessing | [L935](ragcli_ascii_api_surface_examples.md#L935) |
| 4.7 | `ragcli admin corpus publish` | **Backend gap**; suggests `POST /admin/corpus/publish` (also rollback/cleanup) | [L961](ragcli_ascii_api_surface_examples.md#L961) |

---

## 5. Admin observability

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 5.1 | `ragcli admin audit-logs list` | Who did what (audit table) | [L994](ragcli_ascii_api_surface_examples.md#L994) |
| 5.2 | `ragcli admin query-logs list` | Retrieval/query history | [L1023](ragcli_ascii_api_surface_examples.md#L1023) |

---

## 6. Jobs

| § | Command (example) | What the sample shows | Detail |
|---|-------------------|------------------------|--------|
| 6.1 | `ragcli jobs list` | Job index by type/status | [L1052](ragcli_ascii_api_surface_examples.md#L1052) |
| 6.2 | `ragcli jobs status --job-id …` | Failed job with error text; success variant | [L1080](ragcli_ascii_api_surface_examples.md#L1080) |
| 6.3 | `ragcli jobs retry --job-id …` | Retry accepted + new job id | [L1135](ragcli_ascii_api_surface_examples.md#L1135) |

---

## 7. Planned CLI surfaces (backend gaps only)

Reserved commands that must return **`not_supported_by_backend`** until routes exist. Each subsection shows the suggested REST shape.

| § | Command (example) | Suggested API (from sample) | Detail |
|---|-------------------|-----------------------------|--------|
| 7.1 | `ragcli users create --email …` | `POST /users` | [L1174](ragcli_ascii_api_surface_examples.md#L1174) |
| 7.2 | `ragcli users list` | `GET /users` | [L1200](ragcli_ascii_api_surface_examples.md#L1200) |
| 7.3 | `ragcli retrievers list` | `GET /retrievers` | [L1226](ragcli_ascii_api_surface_examples.md#L1226) |
| 7.4 | `ragcli agents list` | `GET /agents` | [L1252](ragcli_ascii_api_surface_examples.md#L1252) |
| 7.5 | `ragcli conversations list` (and create/show) | `GET /conversations` | [L1278](ragcli_ascii_api_surface_examples.md#L1278) |
| 7.6 | `ragcli chat` | `POST /chat` or `/messages` | [L1311](ragcli_ascii_api_surface_examples.md#L1311) |
| 7.7 | `ragcli messages send …` (and list) | `POST /messages` | [L1340](ragcli_ascii_api_surface_examples.md#L1340) |
| 7.8 | `ragcli runs status --run-id …` (and cancel) | `GET /runs/{run_id}` | [L1372](ragcli_ascii_api_surface_examples.md#L1372) |
| 7.9 | `ragcli runs approvals list` (and approve/reject) | `GET /runs/approvals` | [L1404](ragcli_ascii_api_surface_examples.md#L1404) |

---

## 8. Cross-cutting errors

| § | Topic | What the sample shows | Detail |
|---|-------|------------------------|--------|
| 8.1 | Auth required | Gate before protected calls | [L1437](ragcli_ascii_api_surface_examples.md#L1437) |
| 8.2 | Connection failure | Backend unreachable + fix hints | [L1450](ragcli_ascii_api_surface_examples.md#L1450) |
| 8.3 | Base URL mismatch | Warning when `--api-base-url` disagrees with saved session | [L1465](ragcli_ascii_api_surface_examples.md#L1465) |
| 8.4 | Backend API error | HTTP/status + structured invalid request example | [L1473](ragcli_ascii_api_surface_examples.md#L1473) |

---

## 9–10. TUI and implementation rules

| § | Topic | What the sample shows | Detail |
|---|-------|------------------------|--------|
| 9 | TUI retrieved context | `ragcli ui` screen: selection cursor, evidence pane, key bindings | [L1489](ragcli_ascii_api_surface_examples.md#L1489) |
| 10 | Output rules | Human vs JSON contracts; **never** fake backend-gap success | [L1530](ragcli_ascii_api_surface_examples.md#L1530) |

---

## Command keyword finder

Sorted by primary subcommand for quick scanning.

`admin audit-logs list` → [§5.1](ragcli_ascii_api_surface_examples.md#L994) · `admin corpus publish` → [§4.7](ragcli_ascii_api_surface_examples.md#L961) · `admin documents delete` → [§4.5](ragcli_ascii_api_surface_examples.md#L907) · `admin documents index` → [§4.3](ragcli_ascii_api_surface_examples.md#L837) · `admin documents list` → [§4.2](ragcli_ascii_api_surface_examples.md#L808) · `admin documents reindex` → [§4.4](ragcli_ascii_api_surface_examples.md#L872) · `admin documents upload` → [§4.1](ragcli_ascii_api_surface_examples.md#L751) · `admin query-logs list` → [§5.2](ragcli_ascii_api_surface_examples.md#L1023)

`agents list` → [§7.4](ragcli_ascii_api_surface_examples.md#L1252)

`auth me` → [§1.2](ragcli_ascii_api_surface_examples.md#L75)

`chat` → [§7.6](ragcli_ascii_api_surface_examples.md#L1311)

`conversations …` → [§7.5](ragcli_ascii_api_surface_examples.md#L1278)

`documents answer` → [§2.7](ragcli_ascii_api_surface_examples.md#L445) · `documents content` → [§2.9](ragcli_ascii_api_surface_examples.md#L519) · `documents list` → [§2.1](ragcli_ascii_api_surface_examples.md#L151) · `documents page` → [§2.4](ragcli_ascii_api_surface_examples.md#L271) · `documents retrieve` → [§2.5](ragcli_ascii_api_surface_examples.md#L306) · `documents search` → [§2.10](ragcli_ascii_api_surface_examples.md#L549) · `documents show` → [§2.2](ragcli_ascii_api_surface_examples.md#L193) · `documents structure` → [§2.3](ragcli_ascii_api_surface_examples.md#L236)

`jobs list` → [§6.1](ragcli_ascii_api_surface_examples.md#L1052) · `jobs retry` → [§6.3](ragcli_ascii_api_surface_examples.md#L1135) · `jobs status` → [§6.2](ragcli_ascii_api_surface_examples.md#L1080)

`lightrag graphs show` → [§3.4](ragcli_ascii_api_surface_examples.md#L672) · `lightrag labels list` → [§3.1](ragcli_ascii_api_surface_examples.md#L581) · `lightrag labels popular` → [§3.2](ragcli_ascii_api_surface_examples.md#L611) / disabled case [§3.5](ragcli_ascii_api_surface_examples.md#L724) · `lightrag labels search` → [§3.3](ragcli_ascii_api_surface_examples.md#L640)

`login` → [§1.1](ragcli_ascii_api_surface_examples.md#L19) · `logout` → [§1.3](ragcli_ascii_api_surface_examples.md#L118)

`messages …` → [§7.7](ragcli_ascii_api_surface_examples.md#L1340)

`query` (top-level) → [§2.8](ragcli_ascii_api_surface_examples.md#L484)

`retrievers list` → [§7.3](ragcli_ascii_api_surface_examples.md#L1226)

`runs …` / `runs approvals …` → [§7.8](ragcli_ascii_api_surface_examples.md#L1372) · [§7.9](ragcli_ascii_api_surface_examples.md#L1404)

`ui` (TUI) → [§9](ragcli_ascii_api_surface_examples.md#L1489)

`users create` / `users list` → [§7.1](ragcli_ascii_api_surface_examples.md#L1174) · [§7.2](ragcli_ascii_api_surface_examples.md#L1200)

**Errors (no single command):** auth required, connection, base URL warning, API error → [§8](ragcli_ascii_api_surface_examples.md#L1437)
