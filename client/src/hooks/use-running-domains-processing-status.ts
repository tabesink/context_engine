"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { fetchAdminDomainProcessingStatus, type DomainProcessingStatus } from "@/api/processing-status";
import type { KnowledgeGraphDomain } from "@/lib/api/knowledge-graph-admin";
import { getNextProcessingStatusPollDelay } from "@/hooks/use-processing-status";

function isDomainRunning(domain: KnowledgeGraphDomain): boolean {
  const statusLabel = domain.status || (domain.is_healthy ? "running" : "unknown");
  return statusLabel.toLowerCase() === "running" || domain.is_healthy === true;
}

export function useRunningDomainsProcessingStatus(domains: KnowledgeGraphDomain[], enabled = true) {
  const runningDomainIds = useMemo(
    () => domains.filter(isDomainRunning).map((domain) => domain.id),
    [domains],
  );
  const runningKey = runningDomainIds.join(",");
  const [statusByDomain, setStatusByDomain] = useState<Map<string, DomainProcessingStatus>>(() => new Map());
  const statusRef = useRef<Map<string, DomainProcessingStatus>>(new Map());

  useEffect(() => {
    if (!enabled || runningDomainIds.length === 0) {
      statusRef.current = new Map();
      return;
    }

    const timers = new Map<string, number>();
    let cancelled = false;

    const updateStatus = (domainId: string, next: DomainProcessingStatus) => {
      statusRef.current.set(domainId, next);
      setStatusByDomain(new Map(statusRef.current));
    };

    const pollDomain = (domainId: string) => {
      async function run() {
        try {
          const next = await fetchAdminDomainProcessingStatus(domainId);
          if (cancelled) return;
          updateStatus(domainId, next);
          const delay = getNextProcessingStatusPollDelay(next.is_busy, true);
          timers.set(domainId, window.setTimeout(run, delay));
        } catch {
          if (cancelled) return;
          timers.set(domainId, window.setTimeout(run, 30000));
        }
      }

      void run();
    };

    for (const domainId of runningDomainIds) {
      pollDomain(domainId);
    }

    return () => {
      cancelled = true;
      for (const timer of timers.values()) {
        window.clearTimeout(timer);
      }
    };
  }, [enabled, runningKey, runningDomainIds]);

  const effectiveStatusByDomain = useMemo(() => {
    if (!enabled || runningDomainIds.length === 0) return new Map<string, DomainProcessingStatus>();
    const next = new Map<string, DomainProcessingStatus>();
    for (const domainId of runningDomainIds) {
      const status = statusByDomain.get(domainId);
      if (status) next.set(domainId, status);
    }
    return next;
  }, [enabled, runningDomainIds, statusByDomain]);

  return { statusByDomain: effectiveStatusByDomain };
}
