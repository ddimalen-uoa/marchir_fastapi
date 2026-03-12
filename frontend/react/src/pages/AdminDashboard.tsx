import { useAuth } from "../features/auth/useAuth";

export default function AdminDashboard() {
  const { data } = useAuth();

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <p>Welcome, {data?.member.first_name ?? data?.member.upi ?? "Admin"}.</p>
    </div>
  );
}