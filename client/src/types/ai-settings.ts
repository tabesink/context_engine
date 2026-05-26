export type ProviderKind = "openai" | "bedrock_openai" | "ollama";
export type ModelProfileKind = "llm" | "embedding";

export type AIModelProfile = {
  id: string;
  kind: ModelProfileKind;
  provider: ProviderKind;
  display_name: string;
  model: string;
  base_url: string;
  api_key_env_var?: string | null;
  api_key_status: "present" | "missing" | "not_required";
  binding: string;
  dimensions: number | null;
  token_limit: number | null;
  send_dimensions: boolean;
  use_base64: boolean;
  is_enabled: boolean;
  is_default: boolean;
  extra: Record<string, unknown>;
};

export type AISettingsResponse = {
  defaults: {
    llm_profile_id: string;
    embedding_profile_id: string;
  };
  profiles: AIModelProfile[];
  secret_status: Record<string, "present" | "missing">;
};

export type UpdateDefaultsPayload = {
  default_llm_profile_id: string;
  default_embedding_profile_id: string;
};

export type UpsertProviderSecretPayload = {
  value: string;
};

export type CreateProfilePayload = {
  id: string;
  kind: ModelProfileKind;
  provider: ProviderKind;
  display_name: string;
  model: string;
  base_url: string;
  api_key_env_var?: string | null;
  binding: string;
  dimensions?: number | null;
  token_limit?: number | null;
  send_dimensions?: boolean;
  use_base64?: boolean;
  is_enabled?: boolean;
  extra?: Record<string, unknown>;
};

export type UpdateProfilePayload = Partial<Omit<CreateProfilePayload, "id" | "kind" | "provider">>;

export type ModelProfileTestResult = {
  profile_id: string;
  kind: ModelProfileKind;
  success: boolean;
  message: string;
  vector_length?: number | null;
};

