# Frontend Component Contracts

## API Types

```ts
export type DocStatus =
  | 'pending'
  | 'processing'
  | 'preprocessed'
  | 'processed'
  | 'failed'

export type DocStatusResponse = {
  id: string
  content_summary: string
  content_length: number
  status: DocStatus
  created_at: string
  updated_at: string
  track_id?: string
  chunks_count?: number
  error_msg?: string
  metadata?: Record<string, unknown>
  file_path: string
}

export type PipelineStatusResponse = {
  autoscanned: boolean
  busy: boolean
  job_name: string
  job_start?: string
  docs: number
  batchs: number
  cur_batch: number
  request_pending: boolean
  cancellation_requested?: boolean
  latest_message: string
  history_messages?: string[]
  update_status?: Record<string, unknown>
}
```

## DocumentManager

Props:

```ts
type DocumentManagerProps = {}
```

State:

```ts
currentPageDocs: DocStatusResponse[]
pagination: PaginationInfo
statusCounts: Record<string, number>
statusFilter: 'all' | 'processed' | 'analyzing' | 'processing' | 'pending' | 'failed'
sortField: 'created_at' | 'updated_at' | 'id' | 'file_path'
sortDirection: 'asc' | 'desc'
isRefreshing: boolean
selectedDocIds: string[]
```

Responsibilities:

- fetch paginated documents
- show filters/counts
- poll based on `pipelineActive`
- open pipeline status dialog
- open upload dialog
- open document details dialog
- trigger scan/refresh/delete actions if supported

## UploadDocumentsDialog

Props:

```ts
type UploadDocumentsDialogProps = {
  onDocumentsUploaded?: () => Promise<void>
  onUploadBatchAccepted?: () => void
}
```

Responsibilities:

- let user select/drop files
- upload files sequentially or with controlled concurrency
- show transfer progress
- call `onUploadBatchAccepted` after first successful server accept
- call `onDocumentsUploaded` when batch has at least one success

## PipelineStatusDialog

Props:

```ts
type PipelineStatusDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}
```

Responsibilities:

- poll `/documents/pipeline_status` every 2s while open
- show progress and history messages
- request cancellation
- auto-scroll history unless user manually scrolls

## Status Filter Helpers

```ts
export type StatusBucket =
  | 'processed'
  | 'analyzing'
  | 'processing'
  | 'pending'
  | 'failed'

export type StatusFilter = StatusBucket | 'all'

export const getStatusBucket = (status: DocStatus): StatusBucket => {
  if (['preprocessed', 'parsing', 'analyzing'].includes(status)) {
    return 'analyzing'
  }
  if (status === 'processing') return 'processing'
  return status as StatusBucket
}
```

## Backend State Store

```ts
type BackendState = {
  health: boolean
  status: HealthResponse | null
  pipelineBusy: boolean
  pipelineActive: boolean
  lastCheckTime: number
  check: () => Promise<boolean>
}
```

Responsibilities:

- call `/health`
- update `pipelineBusy`
- update `pipelineActive`
- let DocumentManager choose polling cadence
