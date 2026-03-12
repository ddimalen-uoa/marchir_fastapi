import { useEffect, useRef } from "react";
import { Navigate, Outlet } from "react-router";
import { useQueryClient } from "@tanstack/react-query";

import { logoutRequest } from "../../api/authApi";
import { useAuth } from "./useAuth";
import { hasRequiredRole } from "./roleUtils";
import { useAuthStore } from "./authStore";

type RequireRoleProps = {
  allowedRoles: string[];
};

export function RequireRole({ allowedRoles }: RequireRoleProps) {
  const { data, isLoading, isError } = useAuth();
  const queryClient = useQueryClient();
  const setRedirectMessage = useAuthStore((state) => state.setRedirectMessage);
  const handledRef = useRef(false);

  useEffect(() => {
    async function handleRestrictedAccess() {
      if (handledRef.current) return;
      if (!data?.authenticated) return;

      const allowed = hasRequiredRole(data.member.role, allowedRoles);
      if (allowed) return;

      handledRef.current = true;

      try {
        await logoutRequest();
      } catch {
        // ignore backend logout errors; still clear client auth cache
      }

      queryClient.removeQueries({ queryKey: ["auth", "me"] });
      setRedirectMessage("You tried to access a restricted page.");
      window.location.replace("/");
    }

    void handleRestrictedAccess();
  }, [allowedRoles, data, queryClient, setRedirectMessage]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError || !data?.authenticated) {
    return <Navigate to="/" replace />;
  }

  const allowed = hasRequiredRole(data.member.role, allowedRoles);

  if (!allowed) {
    return null;
  }

  return <Outlet />;
}