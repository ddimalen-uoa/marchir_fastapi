import { Outlet } from "react-router";
import { LogoutButton } from "./LogoutButton";

export function AppShell() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex items-center justify-between px-6 py-4 mx-auto max-w-7xl">
        <h1 className="text-2xl font-bold tracking-tight">HCI Assignment Marker</h1>
        <LogoutButton />
      </div>


      <Outlet />

    </div>
  );
}