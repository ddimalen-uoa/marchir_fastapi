import { create } from "zustand";

type UserSelectionState = {
  selectedUserId: string | null;
  selectUser: (id: string) => void;
  clearSelection: () => void;
};

export const useUserSelectionStore = create<UserSelectionState>((set) => ({
  selectedUserId: null,
  selectUser: (id) => set({ selectedUserId: id }),
  clearSelection: () => set({ selectedUserId: null }),
}));