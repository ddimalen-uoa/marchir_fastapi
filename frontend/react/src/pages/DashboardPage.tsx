import { useEffect, useState } from "react";
import { fetchMe, logout } from "../api/api";

type User = {
  upi?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  picture?: string;
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    async function load() {
      const data = await fetchMe();
      console.log(data);
      setAuthenticated(!!data.authenticated);
      setUser(data.member ?? null);
      setLoading(false);
    }

    load();
  }, []);

  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
  };

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>;

  if (!authenticated) {
    return (
      <div style={{ padding: 24 }}>
        <h1>Not logged in</h1>
        <a href="/">Go to login</a>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>Dashboard</h1>
      <p><strong>Name:</strong> {user?.first_name} {user?.last_name}</p>
      <p><strong>Email:</strong> {user?.email}</p>
      <p><strong>UPI:</strong> {user?.upi}</p>

      {user?.picture && (
        <img
          src={user.picture}
          alt="profile"
          width={80}
          height={80}
          style={{ borderRadius: "50%" }}
        />
      )}

      <div style={{ marginTop: 16 }}>
        <button onClick={handleLogout}>Logout</button>
      </div>
    </div>
  );
}