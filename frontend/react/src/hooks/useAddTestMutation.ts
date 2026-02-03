import { useMutation, useQueryClient } from "@tanstack/react-query";
import { addTest, type AddTestRequest, type TestItem } from "../api/test";

export function useAddTestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AddTestRequest) => addTest(payload),

    // Option A (simple): refetch list after success
    // onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),

    // Option B (fast): update cached list immediately (no refetch needed)
    onSuccess: (created: TestItem) => {
      queryClient.setQueryData<TestItem[]>(["users"], (old) => {
        if (!old) return [created];
        return [created, ...old];
      });
    },
  });
}