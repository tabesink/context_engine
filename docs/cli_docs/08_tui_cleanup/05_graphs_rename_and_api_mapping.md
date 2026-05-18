# 5. Rename LightRAG Graphs to Graphs

## 5.1 Decision

Rename the TUI menu label:

```text
LightRAG Graphs
```

to:

```text
Graphs
```

## 5.2 Why

`LightRAG Graphs` leaks implementation details into the operator-facing root menu.

The backend may currently proxy to LightRAG, but the user-facing capability is graph exploration.

## 5.3 Backend Routes Stay the Same Initially

Do not change backend routes as part of this UI cleanup.

Current supported graph routes:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

## 5.4 TUI Screen

Old:

```text
LIGHTRAG GRAPHS
```

New:

```text
GRAPHS
```

Optional subtitle:

```text
Remote graph data from the selected LightRAG domain
```

## 5.5 Future Backend Simplification

Later, the graph API can be cleaned up:

```text
GET /graph
GET /graph/labels?q=&sort=popular&limit=...
```

But do not bundle that with this menu cleanup.

## 5.6 Tests

Update tests that assert screen labels:

- root menu contains `Graphs`
- root menu does not contain `LightRAG Graphs`
- graph screen still calls the same backend routes
- disabled LightRAG still renders backend error unchanged
