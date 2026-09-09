export type Role = "student" | "teacher" | "admin" | (string & {});

export type Member = {
  id: number;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  upi: string | null;
  role: Role | null;
  email_verified: boolean;
};

export type MeResponse = {
  authenticated: true;
  member: Member;
};

export async function getMe(): Promise<MeResponse> {
  const response = await fetch(import.meta.env.VITE_API_URL+"/api/v1/auth/me", {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (response.status === 401) {
    throw new Error("UNAUTHENTICATED");
  }

  if (!response.ok) {
    throw new Error(`GET_ME_FAILED_${response.status}`);
  }

  return response.json() as Promise<MeResponse>;
}

export async function logoutRequest(): Promise<void> {
  const response = await fetch(import.meta.env.VITE_API_URL+"/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`LOGOUT_FAILED_${response.status}`);
  }
}

export type AuthConfig = {
  auth_provider: "sso" | "google";
};

export async function getAuthConfig(): Promise<AuthConfig> {
  const response = await fetch(import.meta.env.VITE_API_URL+"/api/v1/auth/config", {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`AUTH_CONFIG_FAILED_${response.status}`);
  }

  return response.json() as Promise<AuthConfig>;
}

export async function requestEmailLogin(email: string): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(import.meta.env.VITE_API_URL+"/api/v1/auth/email/login", {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new Error(`EMAIL_LOGIN_FAILED_${response.status}`);
  }

  return response.json() as Promise<{ ok: boolean; message: string }>;
}
