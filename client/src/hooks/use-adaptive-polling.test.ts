import { describe, expect, it, vi } from "vitest";

import { createAdaptivePollingController } from "@/hooks/use-adaptive-polling";

describe("createAdaptivePollingController", () => {
  it("runs immediately then schedules using dynamic delay", async () => {
    vi.useFakeTimers();
    const calls: number[] = [];

    const controller = createAdaptivePollingController({
      run: async () => {
        calls.push(Date.now());
        return calls.length;
      },
      getDelay: (result) => (result === 1 ? 25 : 50),
      errorDelayMs: 100,
      initialDelayMs: 0,
    });

    controller.start();
    await vi.runOnlyPendingTimersAsync();
    expect(calls.length).toBe(1);
    await vi.advanceTimersByTimeAsync(25);
    expect(calls.length).toBe(2);
    controller.stop();
    vi.useRealTimers();
  });

  it("uses error delay on failures", async () => {
    vi.useFakeTimers();
    let attempts = 0;

    const controller = createAdaptivePollingController({
      run: async () => {
        attempts += 1;
        if (attempts === 1) throw new Error("fail");
        return attempts;
      },
      getDelay: () => 500,
      errorDelayMs: 40,
      initialDelayMs: 0,
    });

    controller.start();
    await vi.runOnlyPendingTimersAsync();
    expect(attempts).toBe(1);
    await vi.advanceTimersByTimeAsync(39);
    expect(attempts).toBe(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(attempts).toBe(2);
    controller.stop();
    vi.useRealTimers();
  });

  it("stops future polling when stopped", async () => {
    vi.useFakeTimers();
    const run = vi.fn(async () => 1);

    const controller = createAdaptivePollingController({
      run,
      getDelay: () => 20,
      errorDelayMs: 20,
      initialDelayMs: 0,
    });

    controller.start();
    await vi.runOnlyPendingTimersAsync();
    expect(run).toHaveBeenCalledTimes(1);
    controller.stop();
    await vi.advanceTimersByTimeAsync(200);
    expect(run).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
