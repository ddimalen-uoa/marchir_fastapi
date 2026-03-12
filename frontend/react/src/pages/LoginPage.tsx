import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../features/auth/useAuth";
import { dashboardPathForRole } from "../features/auth/roleUtils";
import { useAuthStore } from "../features/auth/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useAuth();

  const redirectMessage = useAuthStore((state) => state.redirectMessage);
  const clearRedirectMessage = useAuthStore((state) => state.clearRedirectMessage);

  useEffect(() => {
    if (data?.authenticated) {
      navigate(dashboardPathForRole(data.member.role), { replace: true });
    }
  }, [data, navigate]);

  function handleLogin() {
    window.location.href = "https://localhost/api/v1/auth/login";
  }

  return (
    <div style={{ padding: 24, fontFamily: "Arial, sans-serif" }}>
      <h1>Login</h1>
      <p>Please sign in to continue.</p>

      {redirectMessage && (
        <div
          style={{
            marginBottom: 16,
            padding: 12,
            border: "1px solid #d97706",
            background: "#fff7ed",
          }}
        >
          {redirectMessage}
        </div>
      )}

      <button onClick={handleLogin} disabled={isLoading}>
        Login with UoA
      </button>

      {redirectMessage && (
        <div style={{ marginTop: 12 }}>
          <button onClick={clearRedirectMessage}>Dismiss</button>
        </div>
      )}
    </div>
  );
}