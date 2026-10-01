import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Check, ChevronDown } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../features/auth/useAuth";
import { dashboardPathForRole } from "../features/auth/roleUtils";
import { useAuthStore } from "../features/auth/authStore";
import {
  getAuthConfig,
  getLoginCourses,
  requestEmailLogin,
  type AuthConfig,
  type LoginCourse,
} from "../api/authApi";
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
  const [courses, setCourses] = useState<LoginCourse[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [courseError, setCourseError] = useState<string | null>(null);
  const [isCoursesLoading, setIsCoursesLoading] = useState(false);
  const [isCourseMenuOpen, setIsCourseMenuOpen] = useState(false);

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
    if (authProvider !== "google") return;

    setIsCoursesLoading(true);
    setCourseError(null);

    getLoginCourses()
      .then((courseList) => setCourses(courseList))
      .catch(() => setCourseError("Courses could not be loaded. Please refresh the page."))
      .finally(() => setIsCoursesLoading(false));
  }, [authProvider]);

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

    if (provider === "google" && !selectedCourseId) {
      const message = "Please select a course before continuing.";
      setCourseError(message);
      window.alert(message);
      return;
    }

    const courseParam = provider === "google"
      ? `&course_id=${encodeURIComponent(selectedCourseId)}`
      : "";

    window.location.href = apiUrl(`/api/v1/auth/login?provider=${provider}${courseParam}`);
  }

  async function handleEmailLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEmailMessage(null);
    setEmailError(null);

    if (!selectedCourseId) {
      const message = "Please select a course before continuing.";
      setCourseError(message);
      window.alert(message);
      return;
    }

    setIsEmailSubmitting(true);

    try {
      const response = await requestEmailLogin(email, Number(selectedCourseId));
      setEmailMessage(response.message);
      setEmail("");
    } catch (error) {
      setEmailError(error instanceof Error ? error.message : "We could not send the email right now. Please try again shortly.");
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

  const selectedCourse = courses.find((course) => String(course.id) === selectedCourseId);

  const formatCourseLabel = (course: LoginCourse) => {
    const code = course.course_code?.trim();
    const name = course.name?.trim();

    if (code && name && code !== name) return `${code} - ${name}`;
    return code || name || `Course ${course.id}`;
  };

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
                     role="alert"
                     className="w-full break-words rounded-lg border border-amber-400 bg-amber-50 p-3 text-left text-sm text-amber-950"
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

                 {authProvider === "google" && (
                   <div className="mb-4 text-left">
                     <label id="course-label" className="mb-2 block text-sm font-medium text-white/80" htmlFor="course-select">
                       Course
                     </label>
                     <Popover.Root open={isCourseMenuOpen} onOpenChange={setIsCourseMenuOpen}>
                       <Popover.Trigger asChild>
                         <button
                           id="course-select"
                           type="button"
                           aria-haspopup="menu"
                           aria-labelledby="course-label course-selection"
                           aria-invalid={Boolean(courseError)}
                           aria-describedby={courseError ? "course-error" : undefined}
                           disabled={isCoursesLoading || courses.length === 0}
                           className="inline-flex min-h-12 w-full items-center justify-between gap-3 rounded-lg border border-blue-500 bg-blue-700 px-4 py-3 text-left text-sm font-medium text-white shadow-sm transition hover:bg-blue-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-300 disabled:cursor-not-allowed disabled:opacity-70"
                         >
                           <span id="course-selection" className="min-w-0 break-words">
                             {isCoursesLoading
                               ? "Loading courses..."
                               : selectedCourse
                                 ? formatCourseLabel(selectedCourse)
                                 : courses.length === 0
                                   ? "No courses available"
                                   : "Select a course"}
                           </span>
                           <ChevronDown aria-hidden="true" className={`h-4 w-4 shrink-0 transition-transform ${isCourseMenuOpen ? "rotate-180" : ""}`} />
                         </button>
                       </Popover.Trigger>
                       <Popover.Portal>
                         <Popover.Content
                           align="start"
                           sideOffset={8}
                           collisionPadding={16}
                           aria-label="Select a course"
                           className="z-50 w-[var(--radix-popover-trigger-width)] overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg"
                         >
                           <ul
                             role="menu"
                             aria-labelledby="course-label"
                             className="max-h-60 overflow-y-auto p-2 text-sm text-gray-700"
                             onKeyDown={(event) => {
                               const keys = ["ArrowDown", "ArrowUp", "Home", "End"];
                               if (!keys.includes(event.key)) return;
                               event.preventDefault();
                               const options = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>("button"));
                               const currentIndex = options.indexOf(document.activeElement as HTMLButtonElement);
                               const nextIndex = event.key === "Home" ? 0
                                 : event.key === "End" ? options.length - 1
                                 : event.key === "ArrowDown" ? (currentIndex + 1) % options.length
                                 : (currentIndex - 1 + options.length) % options.length;
                               options[nextIndex]?.focus();
                             }}
                           >
                             {courses.map((course) => {
                               const isSelected = String(course.id) === selectedCourseId;
                               return (
                                 <li key={course.id} role="none">
                                   <button
                                     type="button"
                                     role="menuitemradio"
                                     aria-checked={isSelected}
                                     onClick={() => {
                                       setSelectedCourseId(String(course.id));
                                       setCourseError(null);
                                       setIsCourseMenuOpen(false);
                                     }}
                                     className={`flex w-full items-center justify-between gap-3 rounded-md px-3 py-2.5 text-left transition focus:bg-gray-100 focus:outline-none ${isSelected ? "bg-blue-50 font-medium text-blue-700 hover:bg-blue-100" : "hover:bg-gray-100 hover:text-gray-900"}`}
                                   >
                                     <span className="min-w-0 break-words">{formatCourseLabel(course)}</span>
                                     <Check aria-hidden="true" className={`h-4 w-4 shrink-0 ${isSelected ? "visible" : "invisible"}`} />
                                   </button>
                                 </li>
                               );
                             })}
                           </ul>
                         </Popover.Content>
                       </Popover.Portal>
                     </Popover.Root>
                     {selectedCourse && (
                       <p className="mt-2 text-xs text-white/60">
                         You will be enrolled in {formatCourseLabel(selectedCourse)}.
                       </p>
                     )}
                     {courseError && (
                       <div id="course-error" role="alert" className="mt-3 rounded-lg border border-amber-500/50 bg-amber-50 px-4 py-3 text-sm text-amber-950">
                         {courseError}
                       </div>
                     )}
                   </div>
                 )}

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
                       <div role="alert" className="mt-4 break-words rounded-lg border border-red-500/40 bg-red-50 px-4 py-3 text-left text-sm text-red-950">
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
