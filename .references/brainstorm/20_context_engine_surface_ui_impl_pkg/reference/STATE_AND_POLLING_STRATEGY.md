# Frontend State and Polling Strategy

## State boundaries

Keep these concerns separate:

| State | Owner | Must not mix with |
|---|---|---|
| Chat messages/retrieval | existing chat session store | processing status polling |
| Context Stream | selected assistant response | source navigator selected node |
| Source Navigator | selected source tree node/context | retrieval filters |
| LightRAG domain selection | domain store | admin lifecycle operations |
| Processing status | new status store/hook | retrieve response adapter |
| Admin settings route | settings shell state | chat composer state |

## Suggested frontend status store shape

```ts
type DomainProcessingStatusState = {
  byDomainId: Record<string, DomainProcessingStatusResponse>;
  loadingByDomainId: Record<string, boolean>;
  errorByDomainId: Record<string, string | undefined>;
  lastFetchedAtByDomainId: Record<string, number | undefined>;
  fetchDomainStatus: (domainId: string, scope: "admin" | "user") => Promise<void>;
};
```

## Polling cadences

| Context | Cadence | Stop condition |
|---|---:|---|
| Admin domain lifecycle screen during active operation | 2–3s | no active job, no pipeline busy, no scanning |
| Admin document processing table | 3–5s | all visible rows terminal |
| Admin jobs screen | 3–5s | no queued/running jobs |
| User chat/workspace domain indicator | 15–30s | domain idle and no failed/processing docs |
| Source navigator selected document badge | 15–30s | selected document indexed/terminal |

## UI placement

- Admin domain route: detailed counters, pipeline banner, action availability, event tail.
- Admin documents route: row-level chips and retry affordance.
- Chat/workspace: subtle domain indexing chip near domain selector or workspace tree.
- SidePanel/SourceNavigator: optional selected document status badge only.

## Error behavior

- `stale=true`: show muted "Status may be stale" chip, not a full error wall.
- `poll_error`: admin can inspect details; regular users see generic unavailable state.
- If status endpoint fails, never break chat retrieval or source navigation.
