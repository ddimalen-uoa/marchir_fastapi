export const ROLE = {
  STUDENT: "student",
  TEACHER: "teacher",
  ADMIN: "admin",
} as const;

export function normalizeRole(role: string | null | undefined): string {
  return (role ?? "").trim().toLowerCase();
}

export function dashboardPathForRole(role: string | null | undefined): string {
  switch (normalizeRole(role)) {
    case ROLE.STUDENT:
      return "/student";
    case ROLE.TEACHER:
      return "/teacher";
    case ROLE.ADMIN:
      return "/admin";
    default:
      return "/";
  }
}

export function hasRequiredRole(
  actualRole: string | null | undefined,
  allowedRoles: readonly string[],
): boolean {
  const normalizedActualRole = normalizeRole(actualRole);
  const normalizedAllowedRoles = allowedRoles.map((role) => normalizeRole(role));
  return normalizedAllowedRoles.includes(normalizedActualRole);
}