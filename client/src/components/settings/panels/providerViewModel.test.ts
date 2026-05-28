import { describe, expect, it } from "vitest";

import { providerIconKind } from "@/components/icons/ProviderIcon";
import {
  mapProviders,
  profileDisplayName,
  providerCatalog,
} from "@/components/settings/panels/providerViewModel";
import type { AIModelProfile, AISettingsResponse } from "@/types/ai-settings";

function makeProfile(overrides: Partial<AIModelProfile>): AIModelProfile {
  return {
    id: "profile-1",
    kind: "llm",
    provider: "openai",
    display_name: "GPT-4o",
    model: "gpt-4o",
    base_url: "https://api.openai.com/v1",
    api_key_status: "missing",
    binding: "openai",
    dimensions: null,
    token_limit: null,
    send_dimensions: false,
    use_base64: false,
    is_enabled: true,
    is_default: false,
    extra: {},
    ...overrides,
  };
}

describe("providerViewModel", () => {
  it("maps OpenAI to missing_key when secret is absent", () => {
    const settings: AISettingsResponse = {
      defaults: { llm_profile_id: "", embedding_profile_id: "" },
      profiles: [],
      secret_status: { OPENAI_API_KEY: "missing" },
    };

    const openai = mapProviders(settings).find((provider) => provider.id === "openai");
    expect(openai?.status).toBe("missing_key");
  });

  it("maps Ollama to healthy when enabled profiles exist", () => {
    const settings: AISettingsResponse = {
      defaults: { llm_profile_id: "", embedding_profile_id: "" },
      profiles: [makeProfile({ provider: "ollama", model: "llama3.2" })],
      secret_status: {},
    };

    const ollama = mapProviders(settings).find((provider) => provider.id === "ollama");
    expect(ollama?.status).toBe("healthy");
    expect(ollama?.profileCount).toBe(1);
  });

  it("returns model id only for profile display", () => {
    expect(profileDisplayName(makeProfile({ model: "gpt-4o", display_name: "GPT-4o" }))).toBe("gpt-4o");
  });

  it("maps bedrock provider id to aws icon kind", () => {
    expect(providerIconKind("bedrock")).toBe("aws");
    expect(providerCatalog.some((provider) => provider.id === "bedrock")).toBe(true);
  });
});
