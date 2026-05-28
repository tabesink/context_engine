import { useEffect, useRef } from "react";

type DelayResolver<T> = (result: T) => number;

type AdaptivePollingControllerOptions<T> = {
  run: () => Promise<T>;
  getDelay: DelayResolver<T>;
  errorDelayMs: number;
  initialDelayMs: number;
  setTimer?: (cb: () => void, delayMs: number) => unknown;
  clearTimer?: (id: unknown) => void;
};

export function createAdaptivePollingController<T>(options: AdaptivePollingControllerOptions<T>) {
  const setTimer = options.setTimer ?? ((cb, delayMs) => setTimeout(cb, delayMs));
  const clearTimer = options.clearTimer ?? ((id) => clearTimeout(id as ReturnType<typeof setTimeout>));
  let timer: unknown = null;
  let stopped = false;

  const schedule = (delayMs: number) => {
    timer = setTimer(async () => {
      try {
        const result = await options.run();
        if (stopped) return;
        schedule(options.getDelay(result));
      } catch {
        if (stopped) return;
        schedule(options.errorDelayMs);
      }
    }, delayMs);
  };

  return {
    start() {
      schedule(options.initialDelayMs);
    },
    stop() {
      stopped = true;
      if (timer !== null) {
        clearTimer(timer);
        timer = null;
      }
    },
  };
}

export function useAdaptivePolling<T>({
  enabled,
  run,
  getDelay,
  errorDelayMs = 30000,
  initialDelayMs = 0,
}: {
  enabled: boolean;
  run: () => Promise<T>;
  getDelay: DelayResolver<T>;
  errorDelayMs?: number;
  initialDelayMs?: number;
}) {
  const runRef = useRef(run);
  const getDelayRef = useRef(getDelay);

  useEffect(() => {
    runRef.current = run;
  }, [run]);

  useEffect(() => {
    getDelayRef.current = getDelay;
  }, [getDelay]);

  useEffect(() => {
    if (!enabled) return;

    const controller = createAdaptivePollingController({
      run: () => runRef.current(),
      getDelay: (result) => getDelayRef.current(result),
      errorDelayMs,
      initialDelayMs,
      setTimer: (cb, delayMs) => window.setTimeout(cb, delayMs),
      clearTimer: (id) => window.clearTimeout(id as number),
    });

    controller.start();
    return () => controller.stop();
  }, [enabled, errorDelayMs, initialDelayMs]);
}
