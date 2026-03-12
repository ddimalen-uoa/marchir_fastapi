import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { logoutRequest } from "../api/authApi";
import { useAuthStore } from "../features/auth/authStore";

export function LogoutButton() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const clearRedirectMessage = useAuthStore((state) => state.clearRedirectMessage);

  async function handleLogout() {
    try {
      await logoutRequest();
    } finally {
      queryClient.removeQueries({ queryKey: ["auth", "me"] });
      clearRedirectMessage();
      navigate("/", { replace: true });
    }
  }

  return <button onClick={handleLogout}>Logout</button>;
}