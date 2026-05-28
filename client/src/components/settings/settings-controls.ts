export const settingsInputClassName = "h-9 rounded-md border-border bg-background shadow-none";
export const settingsSelectTriggerClassName = "h-9 rounded-md border-border bg-background shadow-none";
export const settingsButtonClassName = "rounded-md shadow-none";
export const settingsCompactButtonClassName = "h-8 rounded-md shadow-none";
export const settingsCompactSelectClassName = "h-8 rounded-md border border-border bg-background px-3 text-xs shadow-none";

/** Settings dialog shell — wide enough for sidebar + dual-pane admin layouts. */
export const settingsDialogShellClassName =
  "fixed left-1/2 top-1/2 z-50 h-[min(840px,calc(100vh-48px))] w-[min(1320px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border border-border bg-background p-0 shadow-none outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0";

/** Full-width content wrapper for settings route panels (no artificial max-width cap). */
export const settingsPanelContentClassName = "w-full space-y-5";
