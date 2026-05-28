"use client";

import { StatusChip } from "@/components/surfaces/StatusChip";
import { toneForProcessingStatus } from "@/components/surfaces/status-tone";

export function JobStatusChip({ status }: { status: string }) {
  return <StatusChip label={status} tone={toneForProcessingStatus(status)} />;
}
