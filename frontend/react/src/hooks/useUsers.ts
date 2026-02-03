// hooks/useUsers.ts
import { useQuery } from "@tanstack/react-query";
import { fetchUsers } from "../api/users";

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: fetchUsers,
    staleTime: 60_000,
  });
}