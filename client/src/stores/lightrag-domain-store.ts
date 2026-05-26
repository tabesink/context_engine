"use client";

import { useSyncExternalStore } from "react";
import { fetchLightRagDomains } from "@/lib/lightrag-client";
import type { LightRagDomain } from "@/types/chat";

const DEFAULT_LIGHTRAG_PORT = Number(process.env.NEXT_PUBLIC_LIGHTRAG_DEFAULT_PORT ?? "9621");

type LightRagDomainState = {
  domains: LightRagDomain[];
  selectedPort: number;
  status: "idle" | "loading" | "ready" | "error";
  error?: string;
  loadDomains: () => Promise<void>;
  setSelectedPort: (port: number) => void;
  selectedDomain: LightRagDomain | undefined;
};

const listeners = new Set<() => void>();

let state: LightRagDomainState = {
  domains: [],
  selectedPort: DEFAULT_LIGHTRAG_PORT,
  status: "idle",
  loadDomains,
  setSelectedPort,
  selectedDomain: undefined,
};

function setState(patch: Partial<LightRagDomainState>) {
  state = deriveState({ ...state, ...patch });
  listeners.forEach((listener) => listener());
}

function deriveState(next: LightRagDomainState): LightRagDomainState {
  return {
    ...next,
    selectedDomain: next.domains.find((domain) => domain.port === next.selectedPort),
  };
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return state;
}

async function loadDomains() {
  if (state.status === "loading") return;
  setState({ status: "loading", error: undefined });

  try {
    const domains = await fetchLightRagDomains();
    const selectedIsHealthy = domains.some((domain) => domain.port === state.selectedPort);
    const selectedPort = selectedIsHealthy ? state.selectedPort : domains[0]?.port ?? state.selectedPort;
    setState({ domains, selectedPort, status: "ready" });
  } catch (error) {
    setState({
      status: "error",
      error: error instanceof Error ? error.message : "Could not load Knowledge Graph domains.",
    });
  }
}

function setSelectedPort(port: number) {
  setState({ selectedPort: port });
}

export function useLightRagDomainStore<T = LightRagDomainState>(
  selector: (state: LightRagDomainState) => T = (value) => value as T,
): T {
  return useSyncExternalStore(subscribe, () => selector(getSnapshot()), () => selector(getSnapshot()));
}

export function getSelectedLightRagPort() {
  return state.selectedPort;
}

export function getSelectedLightRagDomainId() {
  return state.selectedDomain?.domain_id ?? "default";
}

export { DEFAULT_LIGHTRAG_PORT };
