import { Outlet } from "react-router";
import { LogoutButton } from "./LogoutButton";

export function AppShell() {
  return (
    <div style={{ padding: 24, fontFamily: "Arial, sans-serif" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <h1 style={{ margin: 0 }}>RISE</h1>
        <LogoutButton />
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}