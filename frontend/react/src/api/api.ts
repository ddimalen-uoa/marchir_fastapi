import { type CourseEnrolled } from "@/types/course";

export async function fetchMe() {
  const res = await fetch("https://localhost/api/v1/auth/me", {
    credentials: "include",
  });

  if (!res.ok) {
    return { authenticated: false };
  }

  return res.json();
}

export async function logout() {
  await fetch("https://localhost/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

export async function getLastSubmission() {
  const res = await fetch("https://localhost/api/v1/marker-result-route/get-last-submission", {
    method: "GET",
    credentials: "include",
  });

  return res;
}


export async function uploadFile(formData: FormData) {
  const response = await fetch("https://localhost/api/v1/upload-route/upload-zip", {
      method: "POST",
      credentials: "include",
      body: formData,
  });

  return response;
}

export async function markAssignment(formData: FormData) {
    const response = await fetch("https://localhost/api/v1/upload-route/submit-assignment", {
      method: "POST",
      credentials: "include",
      body: formData,
  });

  return response;
}

export async function getActiveCoursesStudentsSubmissions() {
  const response = await fetch("https://localhost/api/v1/marker-result-route/get-last-submission/active-with-students-and-submissions", {
    method: "GET",
    credentials: "include",
  });

  return response.json();
}

export async function downloadCourseZip (formData: FormData) {
    const response = await fetch("https://localhost/api/v1/marker-result-route/download-zip-course", {
      method: "POST",
      credentials: "include",
      body: formData,
  });

  return response;
}

export async function downloadCsv (courseId: number) {
  const response = await fetch(`https://localhost/api/v1/marker-result-route/download-marker-results-csv/${courseId}`, {
    method: "GET",
    credentials: "include",
  });

  return response;
}

export async function runAutoEnrollment () {
  const response = await fetch("https://localhost/api/v1/enrollment-route/auto-enroll", {
    method: "GET",
    credentials: "include",
  });

  return response;
}

export async function getCoursesAndEnrollments(): Promise<CourseEnrolled[]> {
  const response = await fetch("https://localhost/api/v1/enrollment-route/get-courses-and-enrollment", {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`FAILED_${response.status}`);
  }

  const data = await response.json();
  return data;
}

export async function addNewCourse (formData: FormData) {
    const response = await fetch("https://localhost/api/v1/course-route/add-course", {
      method: "POST",
      credentials: "include",
      body: formData,
  });

  const data = await response.json();

  return data;
}

export async function updateCourse (formData: FormData, courseId: string) {
    const response = await fetch(`https://localhost/api/v1/course-route/edit-course/${courseId}`, {
      method: "PUT",
      credentials: "include",
      body: formData,
  });

  const data = await response.json();

  return data;
}