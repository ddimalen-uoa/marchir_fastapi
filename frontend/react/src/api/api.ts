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