import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchAuthenticatedAssetBlob, resolveAssetUrl } from "@/lib/api/assets";

describe("asset API helpers", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        localStorage: {
          getItem: vi.fn(() => "asset-token"),
        },
      },
    });
  });

  it("resolves relative asset URLs against the configured API base", () => {
    expect(resolveAssetUrl("/documents/doc-1/assets/asset-1/thumbnail")).toBe(
      "http://127.0.0.1:8010/documents/doc-1/assets/asset-1/thumbnail",
    );
  });

  it("fetches asset blobs through the shared authenticated API boundary", async () => {
    const blob = new Blob(["image-bytes"], { type: "image/png" });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(blob, {
        status: 200,
        headers: { "content-type": "image/png" },
      }),
    );

    const result = await fetchAuthenticatedAssetBlob("/documents/doc-1/assets/asset-1/thumbnail");

    expect(result.type).toBe("image/png");
    await expect(result.text()).resolves.toBe("image-bytes");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/documents/doc-1/assets/asset-1/thumbnail",
      expect.objectContaining({
        credentials: "omit",
        headers: expect.any(Headers),
      }),
    );
    const headers = fetchMock.mock.calls[0]?.[1]?.headers;
    expect(headers).toBeInstanceOf(Headers);
    expect((headers as Headers).get("Authorization")).toBe("Bearer asset-token");
    expect((headers as Headers).get("Accept")).toBe("*/*");
  });
});
