// components/AddTestForm.tsx
import { useAddTestFormStore } from "../stores/useAddTestFormStore";
import { useAddTestMutation } from "../hooks/useAddTestMutation";

export function AddTestForm() {
  const { name, value, setName, setValue, reset } = useAddTestFormStore();
  const addTestMutation = useAddTestMutation();

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    addTestMutation.mutate(
      { name, value },
      {
        onSuccess: () => {
          reset();
        },
      }
    );
  };

  return (
    <form onSubmit={onSubmit} style={{ display: "grid", gap: 8, maxWidth: 420 }}>
      <label>
        Name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Isaac"
        />
      </label>

      <label>
        Value
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="do,a;emasd a;sdlka"
        />
      </label>

      <button type="submit" disabled={addTestMutation.isPending || !name.trim()}>
        {addTestMutation.isPending ? "Saving..." : "Add"}
      </button>

      {addTestMutation.isError && (
        <p style={{ color: "crimson" }}>
          {(addTestMutation.error as Error).message}
        </p>
      )}

      {addTestMutation.isSuccess && <p>Saved ✅</p>}
    </form>
  );
}