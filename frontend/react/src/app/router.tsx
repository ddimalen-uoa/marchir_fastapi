import { createBrowserRouter } from "react-router";

import LoginPage from "../pages/LoginPage";
import StudentDashboard from "../pages/StudentDashboard";
import TeacherDashboard from "../pages/TeacherDashboard/TeacherDashboard";
import AdminDashboard from "../pages/AdminDashboard";
import NotFoundPage from "../pages/NotFoundPage";

import TeacherDashboardReference from "../pages/TeacherDashboardReference";

import { AppShell } from "../components/AppShell";
import { RequireAuth } from "../features/auth/RequireAuth";
import { RequireRole } from "../features/auth/RequireRole";
import { ROLE } from "../features/auth/roleUtils";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LoginPage />,
  },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            element: <RequireRole allowedRoles={[ROLE.STUDENT]} />,
            children: [
              {
                path: "/student",
                element: <StudentDashboard />,
              },
              {
                path: "/student/test",
                element: <TeacherDashboard />,
              },              
              {
                path: "/student/reference",
                element: <TeacherDashboardReference />,
              },
            ],
          },
          {
            element: <RequireRole allowedRoles={[ROLE.TEACHER]} />,
            children: [
              {
                path: "/teacher",
                element: <TeacherDashboard />,                
              },
            ],
          },
          {
            element: <RequireRole allowedRoles={[ROLE.ADMIN]} />,
            children: [
              {
                path: "/admin",
                element: <AdminDashboard />,
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);