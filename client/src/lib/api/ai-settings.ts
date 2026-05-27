import { apiRequest } from "@/lib/api/client";
import type {
  AIModelProfile,
  AISettingsResponse,
  CreateProfilePayload,
  ModelProfileTestResult,
  UpdateDefaultsPayload,
  UpdateProfilePayload,
  UpsertProviderSecretPayload,
} from "@/types/ai-settings";

export const aiSettingsApi = {
  get() {
    return apiRequest<AISettingsResponse>("/admin/ai-settings");
  },
  updateDefaults(payload: UpdateDefaultsPayload) {
    return apiRequest<AISettingsResponse>("/admin/ai-settings/defaults", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  createProfile(payload: CreateProfilePayload) {
    return apiRequest<AIModelProfile>("/admin/ai-settings/profiles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateProfile(profileId: string, payload: UpdateProfilePayload) {
    return apiRequest<AIModelProfile>(`/admin/ai-settings/profiles/${encodeURIComponent(profileId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  testProfile(profileId: string) {
    return apiRequest<ModelProfileTestResult>(
      `/admin/ai-settings/profiles/${encodeURIComponent(profileId)}/test`,
      { method: "POST" },
    );
  },
  setProviderSecret(secretName: string, payload: UpsertProviderSecretPayload) {
    return apiRequest<AISettingsResponse>(
      `/admin/ai-settings/provider-secrets/${encodeURIComponent(secretName)}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    );
  },
  clearProviderSecret(secretName: string) {
    return apiRequest<AISettingsResponse>(
      `/admin/ai-settings/provider-secrets/${encodeURIComponent(secretName)}`,
      {
        method: "DELETE",
      },
    );
  },
};
