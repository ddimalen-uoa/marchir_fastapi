import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, LogOut, ShieldCheck } from "lucide-react";
import { loginAdmin, logoutAdmin } from "../api/authApi";
import { useAdminAuth } from "../features/auth/useAdminAuth";
import AdminDashboard from "./AdminDashboard";
import logo from "../assets/uoa_logo.png";

export default function AdminPage() {
  const { data, isPending, isError } = useAdminAuth();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const session = await loginAdmin(username, password);
      setPassword("");
      queryClient.setQueryData(["auth", "admin"], session);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Admin sign-in failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogout() {
    setError(null);
    setIsSubmitting(true);
    try {
      await logoutAdmin();
      await queryClient.resetQueries({ queryKey: ["auth", "admin"] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Admin sign-out failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isPending) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-100" role="status"><LoaderCircle className="h-6 w-6 animate-spin text-gray-600" aria-label="Loading admin session" /></div>;
  }

  if (data?.authenticated && !isError) {
    return (
      <div className="min-h-screen bg-slate-100">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <span className="text-sm font-medium text-gray-700">{data.admin.username}</span>
          <button type="button" onClick={handleLogout} disabled={isSubmitting} className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            <LogOut className="h-4 w-4" aria-hidden="true" />Sign out
          </button>
        </div>
        {error && <p role="alert" className="mx-auto max-w-7xl px-6 pb-3 text-sm text-red-700">{error}</p>}
        <AdminDashboard />
      </div>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-100 px-6 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-3">
          <img src={logo} alt="University of Auckland" className="h-12 w-28 rounded-md bg-blue-950 px-2 py-1 object-contain" />
          <span className="text-sm font-semibold text-gray-700">HCI Assignment Marker</span>
        </div>
        <div className="mb-6 flex items-center gap-3">
          <ShieldCheck className="h-6 w-6 text-blue-700" aria-hidden="true" />
          <h1 className="text-2xl font-semibold text-gray-900">Admin sign in</h1>
        </div>
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label htmlFor="admin-username" className="mb-2 block text-sm font-medium text-gray-900">Username</label>
            <input id="admin-username" name="username" autoComplete="username" required maxLength={256} value={username} onChange={(event) => setUsername(event.target.value)} className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200" />
          </div>
          <div>
            <label htmlFor="admin-password" className="mb-2 block text-sm font-medium text-gray-900">Password</label>
            <input id="admin-password" name="password" type="password" autoComplete="current-password" required maxLength={1024} value={password} onChange={(event) => setPassword(event.target.value)} className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200" />
          </div>
          {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button type="submit" disabled={isSubmitting} className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-3 text-sm font-medium text-white hover:bg-blue-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-300 disabled:opacity-60">
            {isSubmitting && <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />}
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <Link to="/" className="mt-6 inline-block text-sm text-gray-600 hover:text-blue-700">Back to student and teacher login</Link>
      </div>
    </main>
  );
}
