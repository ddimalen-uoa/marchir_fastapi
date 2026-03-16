import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../features/auth/useAuth";
import { dashboardPathForRole } from "../features/auth/roleUtils";
import { useAuthStore } from "../features/auth/authStore";

import background_image from "../assets/loginbackground2.png";
import logo from "../assets/uoa_logo.png"

export default function LoginPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useAuth();

  const redirectMessage = useAuthStore((state) => state.redirectMessage);
  const clearRedirectMessage = useAuthStore((state) => state.clearRedirectMessage);

  useEffect(() => {
    if (data?.authenticated) {
      navigate(dashboardPathForRole(data.member.role), { replace: true });
    }
  }, [data, navigate]);

  function handleLogin() {
    window.location.href = "https://localhost/api/v1/auth/login";
  }

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

                 <button className="block w-full px-6 py-4 font-semibold text-white transition bg-blue-600 shadow-lg cursor-pointer hover:bg-blue-700 rounded-xl" onClick={handleLogin} disabled={isLoading}>
                    University of Auckland Single Sign-on
                 </button>              

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