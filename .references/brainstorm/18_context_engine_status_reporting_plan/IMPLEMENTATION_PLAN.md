# Context Engine — LightRAG Processing Status Implementation Plan

Audience: coding agent + junior developer  
Goal: add document/domain processing status reporting using LightRAG status concepts while preserving Context Engine as the single API/auth/status boundary.

---

## 0. Non-Negotiable Rules

1. The frontend must not call LightRAG directly.
2. Context Engine remains the only public API boundary.
3. Use existing document rows, job rows, domain registry, and LightRAG adapter.
4. Do not create a second document registry or second job system.
5. Do not expose LightRAG `track_id` as the frontend’s primary contract.
6. User-safe status and admin status must be different projections.
7. Polling must be deduplicated/cached on the backend.
8. Keep status UI separate from retrieval evidence/source navigation UI.
9. Use polling first; do not introduce SSE/WebSockets in this phase.
10. Follow `DESIGN.md`: flat grayscale, no shadows, 12px non-interactive containers, pill-shaped interactive controls, restrained typography.

---

## 1. Target Architecture

```text
Frontend
  Admin Settings / LightRAG Domains
    -> useProcessingStatus(domainId, scope="admin")
    -> GET /admin/lightrag/domains/{domain_id}/processing-status

  Admin Documents / Upload Flow
    -> GET /admin/documents/{document_id}/processing-status
    -> optional domain table from same admin domain status response

  User Chat / Domain Selector / Workspace Tree
    -> useProcessingStatus(domainId, scope="user")
    -> GET /lightrag/domains/{domain_id}/processing-status

Backend
  routes/processing_status.py
    -> ProcessingStatusService
       -> DocumentRepository
       -> JobRepository
       -> LightRAGDomainRegistry / LightRAGDomainService
       -> LightRAGRemoteAdapter.for_domain(domain_id)
          -> /documents/pipeline_status
          -> /documents/status_counts
          -> /documents/track_status/{track_id}
```

---

## 2. Backend Files to Add

### 2.1 `app/schemas/processing_status.py`

Add normalized Pydantic contracts.

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

ProcessingState = Literal[
    "idle",
    "queued",
    "busy",
    "partial_failure",
    "failed",
    "unreachable",
    "unknown",
]

DocumentProcessingState = Literal[
    "uploaded",
    "queued",
    "indexing",
    "ready",
    "failed",
    "deleted",
    "unknown",
]

class ProcessingCounts(BaseModel):
    queued: int = 0
    indexing: int = 0
    ready: int = 0
    failed: int = 0
    deleted: int = 0
    unknown: int = 0

class ActiveProcessingOperation(BaseModel):
    label: str | None = None
    current: int | None = None
    total: int | None = None
    message: str | None = None
    started_at: datetime | None = None

class ProcessingStatusError(BaseModel):
    code: str
    message: str
    source: Literal["context_engine", "lightrag"] = "context_engine"

class DocumentProcessingStatusItem(BaseModel):
    document_id: str
    filename: str
    status: DocumentProcessingState
    domain_id: str | None = None
    job_id: str | None = None
    job_status: str | None = None
    lightrag_status: str | None = None
    message: str | None = None
    can_retry: bool = False
    updated_at: datetime

class LightRAGPipelineStatus(BaseModel):
    reachable: bool
    pipeline_busy: bool = False
    job_name: str | None = None
    job_start: datetime | None = None
    latest_message: str | None = None
    history_tail: list[str] = Field(default_factory=list)
    update_status: dict = Field(default_factory=dict)

class DomainProcessingStatusResponse(BaseModel):
    domain_id: str
    state: ProcessingState
    is_busy: bool
    is_stale: bool = False
    updated_at: datetime
    counts: ProcessingCounts
    active: ActiveProcessingOperation | None = None
    documents: list[DocumentProcessingStatusItem] = Field(default_factory=list)
    lightrag: LightRAGPipelineStatus | None = None
    errors: list[ProcessingStatusError] = Field(default_factory=list)

class DocumentProcessingStatusResponse(BaseModel):
    document: DocumentProcessingStatusItem
    domain: DomainProcessingStatusResponse | None = None
```

Notes:

- The admin route can include `documents`, `lightrag`, and `errors`.
- The user-safe route should omit `documents` or include only safe aggregate counts unless document visibility rules are explicit.
- Never include `track_id` here.

---

### 2.2 `app/services/processing_status_cache.py`

Small in-process TTL cache with per-domain keys. Keep it simple; Redis can come later.

```python
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from threading import Lock
from typing import Any

@dataclass
class CachedStatus:
    value: Any
    expires_at: datetime

class ProcessingStatusCache:
    def __init__(self):
        self._items: dict[str, CachedStatus] = {}
        self._lock = Lock()

    def get(self, key: str):
        now = datetime.now(UTC)
        with self._lock:
            item = self._items.get(key)
            if not item or item.expires_at <= now:
                return None
            return item.value

    def set(self, key: str, value, *, ttl_seconds: int):
        with self._lock:
            self._items[key] = CachedStatus(
                value=value,
                expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
            )

processing_status_cache = ProcessingStatusCache()
```

Keep this cache small and replaceable. It is only an upstream-poll protection layer, not source of truth.

---

### 2.3 `app/services/processing_status_service.py`

This is the main aggregator.

Responsibilities:

- validate domain exists/is available
- list Context Engine documents for the domain
- find related jobs for those documents
- optionally poll LightRAG pipeline/status counts
- normalize statuses
- produce admin/user response projections
- degrade gracefully if LightRAG is unreachable

Pseudo-implementation shape:

```python
from datetime import UTC, datetime
from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus, JobStatus
from app.integrations.lightrag_remote_adapter import LightRAGAdapterError, LightRAGRemoteAdapter
from app.schemas.processing_status import *
from app.services.processing_status_cache import processing_status_cache
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository

class ProcessingStatusService:
    def __init__(self, session: Session):
        self.session = session
        self.documents = DocumentRepository(session)
        self.jobs = JobRepository(session)
        self.domain_registry = LightRAGDomainRegistry()

    def get_domain_status(self, *, domain_id: str, admin: bool) -> DomainProcessingStatusResponse:
        self.domain_registry.validate_available(domain_id)
        documents = self.documents.list_all_by_lightrag_domain(domain_id)
        jobs_by_document = self._latest_jobs_by_document([doc.id for doc in documents])
        local_items = [self._document_item(doc, jobs_by_document.get(doc.id)) for doc in documents]
        local_counts = self._counts(local_items)

        remote_snapshot, stale, errors = self._remote_snapshot(domain_id, local_counts)
        response = self._assemble(domain_id, local_items, local_counts, remote_snapshot, stale, errors)

        if not admin:
            response.documents = []
            response.lightrag = None
            response.errors = [err for err in response.errors if err.code in {"domain_unreachable", "status_stale"}]
        return response
```

Implementation details:

- Add a repository method to fetch latest jobs by document IDs. Do not scan all jobs in Python for large data sets.
- Treat Context Engine document rows as source of truth for document ownership/domain membership.
- Treat LightRAG as an enrichment source, not a replacement registry.

---

## 3. Backend Files to Modify

### 3.1 `app/integrations/lightrag_remote_adapter.py`

Add methods to the existing adapter instead of creating a new HTTP client.

```python
def pipeline_status(self) -> dict[str, Any]:
    data = self.get_json("/documents/pipeline_status")
    if not isinstance(data, dict):
        raise LightRAGInvalidResponse("Invalid LightRAG pipeline status response")
    return data


def status_counts(self) -> dict[str, Any]:
    data = self.get_json("/documents/status_counts")
    if not isinstance(data, dict):
        raise LightRAGInvalidResponse("Invalid LightRAG status counts response")
    return data


def paginated_documents(
    self,
    *,
    page: int = 1,
    page_size: int = 50,
    status_filters: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "page": page,
        "page_size": page_size,
        "sort_field": "updated_at",
        "sort_direction": "desc",
    }
    if status_filters:
        payload["status_filters"] = status_filters
    return self.post_json("/documents/paginated", json=payload)
```

Keep raw response parsing in `ProcessingStatusService`, not frontend.

---

### 3.2 `app/storage/repositories/jobs.py`

Add one small helper.

```python
from sqlalchemy import select


def list_latest_by_document_ids(self, document_ids: list[str]) -> list[JobRow]:
    if not document_ids:
        return []
    # Simple first pass. For small 5–10 user deployments this is acceptable.
    rows = list(
        self.session.scalars(
            select(JobRow)
            .where(JobRow.document_id.in_(document_ids))
            .order_by(JobRow.document_id, JobRow.created_at.desc())
        )
    )
    latest = {}
    for row in rows:
        latest.setdefault(row.document_id, row)
    return list(latest.values())
```

A Postgres `distinct on` optimization can come later; do not over-engineer first pass.

---

### 3.3 `app/api/routes/processing_status.py`

Add one route file for all normalized processing status. This avoids scattering status routes across admin/documents/lightrag route files.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.schemas.processing_status import (
    DomainProcessingStatusResponse,
    DocumentProcessingStatusResponse,
)
from app.services.processing_status_service import ProcessingStatusService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(tags=["processing-status"])

@router.get("/lightrag/domains/{domain_id}/processing-status")
def get_user_domain_processing_status(
    domain_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DomainProcessingStatusResponse:
    del user
    return ProcessingStatusService(session).get_domain_status(domain_id=domain_id, admin=False)

@router.get("/admin/lightrag/domains/{domain_id}/processing-status")
def get_admin_domain_processing_status(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DomainProcessingStatusResponse:
    del admin
    return ProcessingStatusService(session).get_domain_status(domain_id=domain_id, admin=True)

@router.get("/admin/documents/{document_id}/processing-status")
def get_admin_document_processing_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DocumentProcessingStatusResponse:
    del admin
    return ProcessingStatusService(session).get_document_status(document_id=document_id, admin=True)

@router.get("/documents/{document_id}/processing-status")
def get_user_document_processing_status(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentProcessingStatusResponse:
    return ProcessingStatusService(session).get_document_status_for_user(document_id=document_id, user=user)
```

### 3.4 `app/main.py`

Include router.

```python
from app.api.routes import processing_status

app.include_router(processing_status.router)
```

---

## 4. Status Normalization Rules

### 4.1 Document status mapping

| Source | Raw values | Normalized |
|---|---|---|
| Context Engine `DocumentStatus.UPLOADED` | `uploaded` | `uploaded` |
| Context Engine `DocumentStatus.INDEXING` | `indexing` | `indexing` |
| Context Engine `DocumentStatus.READY` | `ready` | `ready` |
| Context Engine `DocumentStatus.FAILED` | `failed` | `failed` |
| Context Engine `DocumentStatus.DELETED` | `deleted` | `deleted` |
| Job queued/running | `queued`, `running` | `queued` / `indexing` |
| LightRAG pending/queued | `PENDING`, `pending`, `queued` | `queued` |
| LightRAG processing | `PROCESSING`, `PARSING`, `ANALYZING`, `PREPROCESSED`, `indexing` | `indexing` |
| LightRAG processed | `PROCESSED`, `processed`, `ready`, `complete` | `ready` |
| LightRAG failed | `FAILED`, `failed`, `error` | `failed` |

### 4.2 Domain state rules

| Condition | Domain `state` |
|---|---|
| LightRAG unreachable and no fresh local active jobs | `unreachable` |
| Any active job or remote pipeline busy | `busy` |
| Any queued docs/jobs but pipeline not busy | `queued` |
| Any failed docs and no active docs | `partial_failure` |
| All ready/deleted and no failures | `idle` |
| Contradictory/missing data | `unknown` |

---

## 5. Backend Polling / Cache Strategy

### 5.1 TTL rules

| Condition | TTL |
|---|---:|
| domain busy / active upload visible | 2–5 seconds |
| domain idle | 15–30 seconds |
| LightRAG unreachable | 10–30 seconds with stale flag |
| admin just performed upload/retry/repair/recreate | allow `force_refresh=true` later if needed |

First pass: no `force_refresh` param required.

### 5.2 Request coalescing

First pass can use simple TTL cache only. If concurrent admin panels still stampede, add one lock per domain key.

Cache key examples:

```text
processing-status:domain:{domain_id}:admin
processing-status:domain:{domain_id}:user
```

Prefer caching the raw remote snapshot, then deriving admin/user projections from fresh local DB rows if possible.

---

## 6. Frontend Files to Add

### 6.1 `client/src/api/processing-status.ts`

```ts
import { apiRequest } from "@/lib/api/client";

export type ProcessingCounts = {
  queued: number;
  indexing: number;
  ready: number;
  failed: number;
  deleted: number;
  unknown: number;
};

export type DomainProcessingStatus = {
  domain_id: string;
  state: "idle" | "queued" | "busy" | "partial_failure" | "failed" | "unreachable" | "unknown";
  is_busy: boolean;
  is_stale: boolean;
  updated_at: string;
  counts: ProcessingCounts;
  active?: {
    label?: string | null;
    current?: number | null;
    total?: number | null;
    message?: string | null;
    started_at?: string | null;
  } | null;
  documents?: Array<{
    document_id: string;
    filename: string;
    status: string;
    domain_id?: string | null;
    job_id?: string | null;
    job_status?: string | null;
    lightrag_status?: string | null;
    message?: string | null;
    can_retry: boolean;
    updated_at: string;
  }>;
  lightrag?: {
    reachable: boolean;
    pipeline_busy: boolean;
    job_name?: string | null;
    job_start?: string | null;
    latest_message?: string | null;
    history_tail: string[];
    update_status: Record<string, unknown>;
  } | null;
  errors: Array<{ code: string; message: string; source: string }>;
};

export function fetchUserDomainProcessingStatus(domainId: string) {
  return apiRequest<DomainProcessingStatus>(
    `/lightrag/domains/${encodeURIComponent(domainId)}/processing-status`,
  );
}

export function fetchAdminDomainProcessingStatus(domainId: string) {
  return apiRequest<DomainProcessingStatus>(
    `/admin/lightrag/domains/${encodeURIComponent(domainId)}/processing-status`,
  );
}
```

---

### 6.2 `client/src/hooks/use-processing-status.ts`

Use a single hook so different components do not create different polling loops.

```ts
import { useEffect, useRef, useState } from "react";
import {
  fetchAdminDomainProcessingStatus,
  fetchUserDomainProcessingStatus,
  type DomainProcessingStatus,
} from "@/api/processing-status";

export function useProcessingStatus({
  domainId,
  admin = false,
  enabled = true,
}: {
  domainId?: string;
  admin?: boolean;
  enabled?: boolean;
}) {
  const [status, setStatus] = useState<DomainProcessingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!domainId || !enabled) return;
    let cancelled = false;

    async function poll() {
      setLoading((current) => current || !status);
      try {
        const next = admin
          ? await fetchAdminDomainProcessingStatus(domainId)
          : await fetchUserDomainProcessingStatus(domainId);
        if (cancelled) return;
        setStatus(next);
        setError(undefined);
        const delay = next.is_busy ? (admin ? 3000 : 5000) : (admin ? 15000 : 30000);
        timer.current = window.setTimeout(poll, delay);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not load processing status.");
        timer.current = window.setTimeout(poll, 30000);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void poll();

    return () => {
      cancelled = true;
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [domainId, admin, enabled]);

  return { status, loading, error };
}
```

Later, replace this with a store if multiple visible components need the same status at the same time.

---

## 7. Frontend UI Changes

### 7.1 Admin LightRAG lifecycle route

Add `DomainProcessingStatusCard`.

Visual requirements:

- flat card
- no shadow
- muted border
- status chips
- compact counters
- recent message tail collapsed by default

Card sections:

1. Header: domain name + state badge.
2. Counter row: queued / indexing / ready / failed.
3. Active operation row: job name, current/total, latest message.
4. Admin-only recent messages: last 3–5 entries.
5. Failed docs affordance: “View failed documents” / “Retry failed” only if existing retry/reingest action is supported.

### 7.2 Admin documents/upload table

Add per-document chip:

- Uploaded
- Queued
- Indexing
- Ready
- Failed
- Deleted

For failed rows, show one admin action:

- Retry job if latest job failed and is `document_ingest`.
- Reingest if document exists and can be reprocessed.

Do not add multiple retry pathways in first pass.

### 7.3 User chat/workspace

Add only a subtle indicator near domain selector/workspace tree:

```text
Knowledge graph: Indexing 2 · Ready 24 · Failed 1
```

If busy:

```text
Indexing in progress — answers may not include newest uploads yet.
```

Do not block querying unless the domain is unreachable.

### 7.4 Source navigator

Optional passive badge only:

```text
Document status: Indexing
```

Do not add polling inside `SidePanel`.

---

## 8. Patch Sequence

### Patch 1 — Backend adapter methods

Files:

- `app/integrations/lightrag_remote_adapter.py`
- tests for adapter using fake `httpx.Client` or existing test pattern

Acceptance:

- Methods call exact LightRAG paths.
- Invalid non-dict responses raise `LightRAGInvalidResponse`.
- Existing retrieval/upload behavior unchanged.

### Patch 2 — Backend schemas

Files:

- `app/schemas/processing_status.py`

Acceptance:

- Schemas import cleanly.
- No route changes yet.

### Patch 3 — Repository helper

Files:

- `app/storage/repositories/jobs.py`

Acceptance:

- Returns latest job per document.
- Existing job tests still pass.

### Patch 4 — ProcessingStatusService

Files:

- `app/services/processing_status_service.py`
- `app/services/processing_status_cache.py`
- service unit tests

Acceptance:

- Aggregates local docs/jobs.
- Uses adapter only through `LightRAGRemoteAdapter.for_domain`.
- Handles LightRAG unavailable by returning stale/partial status with error object.
- Does not expose `track_id`.

### Patch 5 — Routes

Files:

- `app/api/routes/processing_status.py`
- `app/main.py`
- route tests

Acceptance:

- User route requires authenticated user.
- Admin route requires admin.
- Regular user response omits admin-only `documents`, raw LightRAG details, and history tail.
- Admin route includes document list and remote details.

### Patch 6 — Frontend client + hook

Files:

- `client/src/api/processing-status.ts`
- `client/src/hooks/use-processing-status.ts`

Acceptance:

- Uses `apiRequest` only.
- No direct LightRAG URL or port calls.
- Polls slower when idle and faster when busy.

### Patch 7 — Admin UI status card

Files depend on current settings/admin structure. Candidate areas:

- `client/src/components/settings/`
- `client/src/components/admin/`
- existing LightRAG domain lifecycle panel

Acceptance:

- Shows state badge, counts, active operation, latest message.
- Does not mix with chat right panel.
- Styling follows `DESIGN.md`.

### Patch 8 — User-safe domain indicator

Files:

- domain selector component or `LightRagChatShell.tsx`
- optional small `DomainProcessingIndicator.tsx`

Acceptance:

- No blocking behavior unless domain unreachable.
- No admin-only details shown.
- Polling only while chat/workspace shell is mounted.

---

## 9. Tests

### Backend tests

Add:

- `tests/test_lightrag_remote_adapter_status.py`
- `tests/test_processing_status_service.py`
- `tests/test_processing_status_routes.py`

Test cases:

1. `pipeline_status()` maps dict response.
2. `status_counts()` maps dict response.
3. Invalid LightRAG status response raises adapter error.
4. Domain status aggregates document rows by status.
5. Latest job is attached to document item.
6. LightRAG unreachable returns `is_stale=true` and `errors`, not a 500.
7. User route hides admin-only fields.
8. Admin route requires admin.
9. `track_id` never appears in serialized response.
10. Idle/busy state rules are deterministic.

### Frontend validation

Run:

```bash
cd client
npm run lint
npm run build
```

If test framework exists, add:

- polling hook schedules shorter delay when `is_busy=true`
- polling hook backs off on error
- admin card renders counts and active operation
- user indicator hides admin-only fields

---

## 10. Validation Commands

Backend:

```bash
python -m pytest -q
python -m pytest tests/test_lightrag_remote_adapter_status.py -q
python -m pytest tests/test_processing_status_service.py -q
python -m pytest tests/test_processing_status_routes.py -q
```

Frontend:

```bash
cd client
npm run lint
npm run build
```

Manual checks:

1. Admin uploads a document to a healthy LightRAG domain.
2. Admin domain card changes from queued/indexing to ready or failed.
3. Regular user sees only safe aggregate indicator.
4. Multiple browser sessions polling same domain do not create excessive upstream LightRAG calls.
5. Stopping LightRAG domain results in stale/unreachable status, not UI crash.
6. Existing chat retrieval still works.
7. Existing Source Navigator still works.
8. No frontend code calls LightRAG directly.

---

## 11. Open Questions for Developer to Resolve in Codebase

1. Where is the current admin settings route/component for LightRAG lifecycle management? Add `DomainProcessingStatusCard` there.
2. Does the project already have a frontend test runner? If not, skip component tests and rely on lint/build.
3. Should the user-safe route show all domain counts or only aggregate busy/ready/failed? Recommended: counts are safe, raw messages are not.
4. Should `GET /documents/{document_id}/ingestion-status` stay as-is? Recommended: yes, add `/processing-status` as the cleaner future-facing alias.
5. Is RQ scheduler currently calling `poll_lightrag_statuses()`? If yes, coordinate with new status service so polling does not duplicate remote calls unnecessarily.

---

## 12. Definition of Done

Done means:

- no frontend direct LightRAG calls
- one normalized processing status schema
- one processing status service
- existing jobs/document/domain systems reused
- status routes tested for auth boundaries
- backend returns partial/stale status when LightRAG is unreachable
- admin UI shows domain/document progress
- user UI shows safe domain indexing indicator
- status polling is visibility-aware and backend-cached
- existing retrieval, source tree, Source Navigator, and AssetCards continue to work

