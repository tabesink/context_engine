import { describe, expect, it } from "vitest";

import { getNextProcessingStatusPollDelay } from "@/hooks/use-processing-status";

describe("processing-status polling", () => {
  it("uses shorter delays when busy", () => {
    expect(getNextProcessingStatusPollDelay(true, true)).toBe(3000);
    expect(getNextProcessingStatusPollDelay(true, false)).toBe(5000);
  });

  it("uses longer delays when idle", () => {
    expect(getNextProcessingStatusPollDelay(false, true)).toBe(15000);
    expect(getNextProcessingStatusPollDelay(false, false)).toBe(30000);
  });
});
