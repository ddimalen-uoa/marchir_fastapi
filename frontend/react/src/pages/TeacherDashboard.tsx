import { useAuth } from "../features/auth/useAuth";

export default function TeacherDashboard() {
  const { data } = useAuth();

  return (
    <div>
      <h2>Teacher Dashboard</h2>
      <p>Welcome, {data?.member.first_name ?? data?.member.upi ?? "Teacher"}.</p>
    </div>
  );
}