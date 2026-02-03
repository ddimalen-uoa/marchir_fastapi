export type User = {
  id: string;
  name: string;
  value: string;
};

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch("/api/v1/test-route/");
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}