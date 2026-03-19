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

export async function markAssginment(formData: FormData) {
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