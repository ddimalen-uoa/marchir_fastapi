import { useAuth } from "../features/auth/useAuth";

export default function StudentDashboard() {
  const { data } = useAuth();

  return (
    <div>
      <h2>Student Dashboard</h2>
      <p>Welcome, {data?.member.first_name ?? data?.member.upi ?? "Student"}.</p>
    </div>
  );
}