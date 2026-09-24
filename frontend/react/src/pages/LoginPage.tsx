import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../features/auth/useAuth";
import { dashboardPathForRole } from "../features/auth/roleUtils";
import { useAuthStore } from "../features/auth/authStore";
import { getAuthConfig, requestEmailLogin, type AuthConfig } from "../api/authApi";
import { apiUrl } from "../api/apiUrl";

import background_image from "../assets/loginbackground2.png";
import logo from "../assets/uoa_logo.png"

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data, isLoading } = useAuth();
  const [authProvider, setAuthProvider] = useState<AuthConfig["auth_provider"] | null>(null);
  const [authConfigError, setAuthConfigError] = useState(false);
  const [email, setEmail] = useState("");
  const [emailMessage, setEmailMessage] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [isEmailSubmitting, setIsEmailSubmitting] = useState(false);

  const redirectMessage = useAuthStore((state) => state.redirectMessage);
  const setRedirectMessage = useAuthStore((state) => state.setRedirectMessage);
  const clearRedirectMessage = useAuthStore((state) => state.clearRedirectMessage);

  useEffect(() => {
    if (data?.authenticated) {
      navigate(dashboardPathForRole(data.member.role), { replace: true });
    }
  }, [data, navigate]);

  useEffect(() => {
    getAuthConfig()
      .then((config) => setAuthProvider(config.auth_provider))
      .catch(() => setAuthConfigError(true));
  }, []);

  useEffect(() => {
    const message = searchParams.get("message");
    if (message) {
      setRedirectMessage(message);
      setSearchParams((params) => {
        params.delete("message");
        return params;
      }, { replace: true });
    }
  }, [searchParams, setRedirectMessage, setSearchParams]);

  function handleLogin(provider = authProvider) {
    if (!provider) return;
    window.location.href = apiUrl(`/api/v1/auth/login?provider=${provider}`);
  }

  async function handleEmailLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEmailMessage(null);
    setEmailError(null);
    setIsEmailSubmitting(true);

    try {
      const response = await requestEmailLogin(email);
      setEmailMessage(response.message);
      setEmail("");
    } catch {
      setEmailError("We could not send the email right now. Please try again shortly.");
    } finally {
      setIsEmailSubmitting(false);
    }
  }

  const providerLabel = authConfigError
    ? "Sign-in unavailable"
    : authProvider === "google"
      ? "Continue with Google"
      : authProvider === "sso"
        ? "University of Auckland Single Sign-on"
        : "Loading sign-in...";

  return (
    <>
        <div className="absolute inset-0">
          <img
            src={background_image}
            className="object-cover w-full h-full"
            alt="Campus background"
          />
        </div>
        <div className="absolute inset-0 bg-black/70"></div>

          <div className="relative z-10 flex items-center justify-center min-h-screen p-6">

            <div className="w-full max-w-md p-10 text-center border shadow-2xl backdrop-blur-md bg-white/10 border-white/20 rounded-2xl">

              <div className="flex flex-col items-center gap-4 mb-8">

                <div className="flex items-center justify-center w-40 h-16 text-xl font-bold text-white rounded-full">
                  <img
                  src={logo}
                  />
                </div>

                 {redirectMessage && (
                   <div
                     style={{
                       marginBottom: 16,
                       padding: 12,
                       border: "1px solid #d97706",
                      background: "#fff7ed",
                     }}
                   >
                     {redirectMessage}
                   </div>
                 )}

                <h1 className="text-xl font-semibold text-white">
                  HCI Assignment Marker
                </h1>

                <p className="text-sm text-white/70">
                  Secure access portal
                </p>

              </div>

                 <button className="block w-full px-6 py-4 font-semibold text-white transition bg-blue-600 shadow-lg cursor-pointer hover:bg-blue-700 rounded-xl" onClick={() => handleLogin()} disabled={isLoading || !authProvider || authConfigError}>
                    {providerLabel}
                 </button>

                 {authConfigError && (
                   <div className="mt-4 rounded-lg border border-red-500/40 bg-red-50 px-4 py-3 text-left text-sm text-red-950">
                     The sign-in configuration could not be loaded. Please refresh the page or contact support.
                   </div>
                 )}

                 {authProvider === "google" && (
                   <>
                     <div className="flex items-center gap-3 my-6 text-xs uppercase tracking-wider text-white/60">
                       <div className="h-px flex-1 bg-white/20"></div>
                       <span>or use email</span>
                       <div className="h-px flex-1 bg-white/20"></div>
                     </div>

                     <form onSubmit={handleEmailLogin} className="space-y-3 text-left">
                       <label className="block text-sm font-medium text-white/80" htmlFor="email-login">
                         Email address
                       </label>
                       <input
                         id="email-login"
                         className="w-full rounded-lg border border-white/30 bg-white/90 px-4 py-3 text-slate-950 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-300"
                         type="email"
                         value={email}
                         onChange={(event) => setEmail(event.target.value)}
                         placeholder="name@example.com"
                         required
                       />
                       <button
                         className="block w-full rounded-xl bg-white px-6 py-3 font-semibold text-slate-950 shadow-lg transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-70"
                         type="submit"
                         disabled={isEmailSubmitting}
                       >
                         {isEmailSubmitting ? "Sending email..." : "Send email link"}
                       </button>
                     </form>

                     {emailMessage && (
                       <div className="mt-4 rounded-lg border border-emerald-500/40 bg-emerald-50 px-4 py-3 text-left text-sm text-emerald-950">
                         {emailMessage}
                       </div>
                     )}

                     {emailError && (
                       <div className="mt-4 rounded-lg border border-red-500/40 bg-red-50 px-4 py-3 text-left text-sm text-red-950">
                         {emailError}
                       </div>
                     )}
                   </>
                 )}

                 {redirectMessage && (
                   <div style={{ marginTop: 12 }}>
                    <button onClick={clearRedirectMessage}>Dismiss</button>
                   </div>
                 )}

            </div>

          </div>
    </>
  );
}
