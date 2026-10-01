import { useQuery } from "@tanstack/react-query";
import { getAdminSession } from "../../api/authApi";

export function useAdminAuth() {
  return useQuery({
    queryKey: ["auth", "admin"],
    queryFn: getAdminSession,
    retry: false,
  });
}
