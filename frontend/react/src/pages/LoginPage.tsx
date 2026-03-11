export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = "https://localhost/api/v1/auth/login";
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Login</h1>
      <button onClick={handleLogin}>Login with OAuth Provider</button>
    </div>
  );
}