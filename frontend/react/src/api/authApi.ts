export type Role = "student" | "teacher" | "admin" | (string & {});

export type Member = {
  id: number;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  upi: string | null;
  role: Role | null;
};

export type MeResponse = {
  authenticated: true;
  member: Member;
};

export async function getMe(): Promise<MeResponse> {
  const response = await fetch("https://localhost/api/v1/auth/me", {
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
  const response = await fetch("https://localhost/api/v1/auth/logout", {
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