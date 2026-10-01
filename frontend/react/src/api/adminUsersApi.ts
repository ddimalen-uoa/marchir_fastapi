import { apiUrl } from "./apiUrl";

export type UserEnrollment = {
  id: number;
  course_id: number;
  course_name: string;
  course_code: string;
  has_submission: boolean;
};

export type AdminUser = {
  id: number;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  upi: string | null;
  role: string | null;
  is_active: boolean;
  email_verified: boolean;
  created: string | null;
  enrollments: UserEnrollment[];
  teacher_courses: AdminCourse[];
};

export type UserChanges = {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  upi: string | null;
  role: "student" | "teacher";
  is_active: boolean;
};

export type AdminCourse = { id: number; name: string; course_code: string; is_active: boolean };
export type UserList = { items: AdminUser[]; total: number; page: number; page_size: number };

async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(apiUrl(`/api/v1/${path}`), {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : "The request could not be completed. Please try again.");
  }
  return response.json() as Promise<T>;
}

export const listAdminUsers = (params: URLSearchParams) => request<UserList>(`admin/users?${params}`);
export const listAdminCourses = () => request<AdminCourse[]>("enrollment-route/get-courses-and-enrollment");
export const updateAdminUser = (id: number, changes: UserChanges) => request(`admin/users/${id}`, "PATCH", changes);
export const moveAdminUser = (id: number, enrollmentId: number | null, courseId: number) => request(`admin/users/${id}/course`, "POST", { enrollment_id: enrollmentId, course_id: courseId });
export const assignTeacherCourses = (id: number, courseIds: number[]) => request(`admin/users/${id}/teacher-courses`, "PUT", { course_ids: courseIds });
