// stores/useAddTestFormStore.ts
import { create } from "zustand";

type AddTestFormState = {
  name: string;
  value: string;
  setName: (name: string) => void;
  setValue: (value: string) => void;
  reset: () => void;
};

export const useAddTestFormStore = create<AddTestFormState>((set) => ({
  name: "",
  value: "",
  setName: (name) => set({ name }),
  setValue: (value) => set({ value }),
  reset: () => set({ name: "", value: "" }),
}));