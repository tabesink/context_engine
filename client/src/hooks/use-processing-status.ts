"use client";

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
  const statusRef = useRef<DomainProcessingStatus | null>(null);

  useEffect(() => {
    if (!domainId || !enabled) return;
    const activeDomainId = domainId;
    let cancelled = false;

    async function poll() {
      setLoading((current) => current || !statusRef.current);
      try {
        const next = admin
          ? await fetchAdminDomainProcessingStatus(activeDomainId)
          : await fetchUserDomainProcessingStatus(activeDomainId);
        if (cancelled) return;
        setStatus(next);
        statusRef.current = next;
        setError(undefined);
        const delay = getNextProcessingStatusPollDelay(next.is_busy, admin);
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

export function getNextProcessingStatusPollDelay(isBusy: boolean, admin: boolean) {
  if (isBusy) return admin ? 3000 : 5000;
  return admin ? 15000 : 30000;
}
