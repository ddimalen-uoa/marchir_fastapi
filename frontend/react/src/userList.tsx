import { useUsers } from "./hooks/useUsers";
import { useUserSelectionStore } from "./stores/useUserSelectionStore";

export function UsersList() {
  const { data, isLoading, isError } = useUsers();
  const { selectedUserId, selectUser } = useUserSelectionStore();

  if (isLoading) return <p>Loading...</p>;
  if (isError) return <p>Error loading users</p>;

  return (
    <ul>
      {data!.map((user) => (
        <li
          key={user.id}
          onClick={() => selectUser(user.id)}
          style={{
            cursor: "pointer",
            fontWeight: user.id === selectedUserId ? "bold" : "normal",
          }}
        >
          {user.name} ({user.value})
        </li>
      ))}
    </ul>
  );
}