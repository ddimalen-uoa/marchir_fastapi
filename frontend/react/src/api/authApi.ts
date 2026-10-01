import { apiUrl } from "./apiUrl";

export type AdminSession = {
  authenticated: true;
  admin: { username: string; role: "admin" };
};

async function adminRequest(path: string, credentials?: { username: string; password: string }): Promise<AdminSession> {
  const response = await fetch(apiUrl(`/api/v1/auth/admin/${path}`), {
    method: credentials ? "POST" : "GET",
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...(credentials ? { body: JSON.stringify(credentials) } : {}),
  });
  if (!response.ok) {
    const message = response.status === 401 ? "Invalid admin username or password."
      : response.status === 429 ? "Too many attempts. Please wait a minute before trying again."
      : response.status === 503 ? "Admin login is not configured."
      : "Admin sign-in is unavailable. Please try again.";
    throw new Error(message);
  }
  return response.json() as Promise<AdminSession>;
}

export const getAdminSession = () => adminRequest("me");
export const loginAdmin = (username: string, password: string) => adminRequest("login", { username, password });

export async function logoutAdmin(): Promise<void> {
  const response = await fetch(apiUrl("/api/v1/auth/admin/logout"), {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) throw new Error("Admin sign-out failed. Please try again.");
}

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
  const response = await fetch(apiUrl("/api/v1/auth/me"), {
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
  const response = await fetch(apiUrl("/api/v1/auth/logout"), {
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

export type LoginCourse = {
  id: number;
  name: string | null;
  course_code: string | null;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
};

export async function getAuthConfig(): Promise<AuthConfig> {
  const response = await fetch(apiUrl("/api/v1/auth/config"), {
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

export async function getLoginCourses(): Promise<LoginCourse[]> {
  const response = await fetch(apiUrl("/api/v1/course-route/active"), {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`LOGIN_COURSES_FAILED_${response.status}`);
  }

  return response.json() as Promise<LoginCourse[]>;
}

export async function requestEmailLogin(
  email: string,
  courseId: number,
): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(apiUrl("/api/v1/auth/email/login"), {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, course_id: courseId }),
  });

  if (!response.ok) {
    if (response.status === 403) {
      const error = await response.json().catch(() => ({}));
      if (typeof error.detail === "string") throw new Error(error.detail);
    }
    throw new Error("We could not send the email right now. Please try again shortly.");
  }

  return response.json() as Promise<{ ok: boolean; message: string }>;
}
