import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { StoreApi, UseBoundStore } from "zustand";

type WithSelectors<S> = S extends { getState: () => infer T }
  ? S & { use: { [K in keyof T]: () => T[K] } }
  : never;

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function errorMessage(error: unknown, fallback = "Request failed") {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function createSelectors<S extends UseBoundStore<StoreApi<object>>>(store: S): WithSelectors<S> {
  const withSelectors = store as WithSelectors<S>;
  withSelectors.use = {} as WithSelectors<S>["use"];
  for (const key of Object.keys(store.getState())) {
    (withSelectors.use as Record<string, () => unknown>)[key] = () =>
      store((state) => state[key as keyof typeof state]);
  }
  return withSelectors;
}
