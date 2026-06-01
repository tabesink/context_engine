import { beforeEach, describe, expect, it, vi } from "vitest";

import { APIError } from "@/lib/api/client";
import { queryGraphs } from "@/api/lightrag";

describe("LightRAG graph API", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("surfaces backend failures through the shared API error contract", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Graph service unavailable" }), {
        status: 503,
        statusText: "Service Unavailable",
        headers: { "content-type": "application/json" },
      }),
    );

    const request = queryGraphs("Safety", 2, 25);

    await expect(request).rejects.toBeInstanceOf(APIError);
    await expect(request).rejects.toMatchObject({
      status: 503,
      body: { detail: "Graph service unavailable" },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/lightrag/domains/default/graphs?label=Safety&max_depth=2&max_nodes=25",
      expect.objectContaining({
        credentials: "omit",
      }),
    );
  });
});
