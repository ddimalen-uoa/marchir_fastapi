import { create } from "zustand";

type AuthStore = {
  redirectMessage: string | null;
  setRedirectMessage: (message: string | null) => void;
  clearRedirectMessage: () => void;
};

export const useAuthStore = create<AuthStore>((set) => ({
  redirectMessage: null,
  setRedirectMessage: (message) => set({ redirectMessage: message }),
  clearRedirectMessage: () => set({ redirectMessage: null }),
}));