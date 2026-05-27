import { apiRequest } from "@/lib/api/client";
import type { CurrentUser, LoginPayload } from "@/types/user";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export const authApi = {
  login(payload: LoginPayload) {
    return apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: false,
    });
  },
  me() {
    return apiRequest<CurrentUser>("/auth/me");
  },
  async logout() {
    return Promise.resolve();
  },
};
