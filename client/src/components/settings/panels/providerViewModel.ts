import type { AIModelProfile, AISettingsResponse, ProviderKind } from "@/types/ai-settings";
import type { ProviderIconId } from "@/components/icons/ProviderIcon";
import { providerIconKind, type ProviderIconKind } from "@/components/icons/ProviderIcon";

export type ProviderId = ProviderIconId;
export type ProviderStatus = "healthy" | "missing_key" | "local" | "no_profiles";

export type ProviderListItemVM = {
  id: ProviderId;
  providerKind: ProviderKind;
  name: string;
  profileCount: number;
  status: ProviderStatus;
  requiresCredential: boolean;
  secretName?: string;
  helperText: string;
  credentialPlaceholder: string;
};

export const providerCatalog: ProviderListItemVM[] = [
  {
    id: "openai",
    providerKind: "openai",
    name: "OpenAI",
    profileCount: 0,
    status: "missing_key",
    requiresCredential: true,
    secretName: "OPENAI_API_KEY",
    helperText: "Used by OpenAI LLM and embedding profiles.",
    credentialPlaceholder: "Enter OpenAI API key",
  },
  {
    id: "bedrock",
    providerKind: "bedrock_openai",
    name: "AWS Bedrock",
    profileCount: 0,
    status: "missing_key",
    requiresCredential: true,
    secretName: "AWS_BEARER_TOKEN_BEDROCK",
    helperText: "Required for Bedrock OpenAI-compatible LLM profiles.",
    credentialPlaceholder: "Enter AWS bearer token",
  },
  {
    id: "ollama",
    providerKind: "ollama",
    name: "Ollama",
    profileCount: 0,
    status: "local",
    requiresCredential: false,
    helperText: "No API key required. Configure local Ollama model endpoints in model profiles.",
    credentialPlaceholder: "No credential required",
  },
];

export function statusLabel(status: ProviderStatus): string {
  if (status === "healthy") return "Healthy";
  if (status === "missing_key") return "Missing key";
  if (status === "local") return "Local";
  return "No profiles";
}

export function profileDisplayName(profile: AIModelProfile): string {
  return profile.model;
}

export function mapProviders(settings: AISettingsResponse | null): ProviderListItemVM[] {
  const profiles = settings?.profiles ?? [];
  const secretStatus = settings?.secret_status ?? {};

  return providerCatalog.map((base) => {
    const profileCount = profiles.filter((item) => item.provider === base.providerKind && item.is_enabled).length;

    let status: ProviderStatus;
    if (base.id === "ollama") {
      status = profileCount > 0 ? "healthy" : "local";
    } else {
      const secret = base.secretName ? secretStatus[base.secretName] : "missing";
      if (secret === "missing") {
        status = "missing_key";
      } else if (profileCount === 0) {
        status = "no_profiles";
      } else {
        status = "healthy";
      }
    }

    return {
      ...base,
      profileCount,
      status,
    };
  });
}

export function sortProfilesForProvider(profiles: AIModelProfile[], provider: ProviderKind): AIModelProfile[] {
  return profiles
    .filter((item) => item.provider === provider && item.is_enabled)
    .sort((a, b) => {
      if (a.is_default !== b.is_default) return Number(b.is_default) - Number(a.is_default);
      return a.model.localeCompare(b.model);
    });
}

export { providerIconKind, type ProviderIconKind };
