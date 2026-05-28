import { describe, expect, it, vi } from "vitest";

const { apiRequest } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest,
}));

import {
  fetchAdminDomainDocumentsProcessingStatus,
  fetchAdminDomainProcessingStatus,
  fetchUserDomainProcessingStatus,
} from "@/api/processing-status";

describe("processing-status api", () => {
  it("calls user processing-status endpoint", async () => {
    apiRequest.mockResolvedValueOnce({});
    await fetchUserDomainProcessingStatus("default");
    expect(apiRequest).toHaveBeenCalledWith("/lightrag/domains/default/processing-status");
  });

  it("calls admin processing-status endpoint", async () => {
    apiRequest.mockResolvedValueOnce({});
    await fetchAdminDomainProcessingStatus("default");
    expect(apiRequest).toHaveBeenCalledWith("/admin/lightrag/domains/default/processing-status");
  });

  it("calls admin domain documents processing-status endpoint with pagination", async () => {
    apiRequest.mockResolvedValueOnce({});
    await fetchAdminDomainDocumentsProcessingStatus("default", { limit: 25, offset: 10 });
    expect(apiRequest).toHaveBeenCalledWith(
      "/admin/lightrag/domains/default/documents/processing-status?limit=25&offset=10",
    );
  });
});
