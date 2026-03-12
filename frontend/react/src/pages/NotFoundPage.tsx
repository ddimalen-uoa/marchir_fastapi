import { Link } from "react-router";

export default function NotFoundPage() {
  return (
    <div style={{ padding: 24 }}>
      <h2>Page not found</h2>
      <p>The page you requested does not exist.</p>
      <Link to="/">Go to Login</Link>
    </div>
  );
}