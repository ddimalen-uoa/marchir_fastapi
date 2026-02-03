// api/test.ts
export type AddTestRequest = {
  name: string;
  value: string;
};

export type TestItem = {
  id: string;
  name: string;
  value: string;
};

export async function addTest(payload: AddTestRequest): Promise<TestItem> {
  const res = await fetch("/api/v1/test-route/add-test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    // Try to extract FastAPI error detail
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail ?? "Failed to add test");
  }

  return res.json();
}