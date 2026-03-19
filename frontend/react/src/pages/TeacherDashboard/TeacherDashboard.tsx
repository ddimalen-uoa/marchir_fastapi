import { useEffect, useMemo, useState } from "react";
import { 
  BookOpen, 
  Users,
  FileSpreadsheet
} from "lucide-react";
import { useAuth } from "@/features/auth/useAuth";

import StatCard from "./components/StatCard";
import { getActiveCoursesStudentsSubmissions, downloadCourseZip, downloadCsv } from "@/api/api";
import type { Course } from "@/types/course";

export default function TeacherDashboard() {
  const { data } = useAuth();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleCSVDownload = async (courseId: number) => {
      const response = await downloadCsv(courseId);

      if (!response.ok) {
        throw new Error("Failed to download CSV");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "marker_results.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();

      window.URL.revokeObjectURL(url);
  }


  const handleZipDownload = async (course: string) => {
        try {
        const formData = new FormData();
        formData.append("course", course);

        const response = await downloadCourseZip(formData);

        if (!response.ok) {
          throw new Error("Failed to download zip");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = `${course.replace(/\./g, "")}.zip`;
        document.body.appendChild(link);
        link.click();
        link.remove();

        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
      }
  }

  useEffect(() => {
    const loadCourses = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const result = await getActiveCoursesStudentsSubmissions();
        setCourses(result.courses);

        if (result.courses.length > 0) {
          setSelectedCourseId(result.courses[0].id);
        } else {
          setSelectedCourseId(null);
        }
      } catch (err) {
        console.error("Failed to load courses:", err);
        setError("Failed to load courses.");
      } finally {
        setIsLoading(false);
      }
    };

    loadCourses();
  }, []);

  const totalSubmissions = useMemo(() => {
    return courses.reduce(
      (sum, course) => sum + course.submitted_students.length,
      0
    );
  }, [courses]);

  const totalCourses = courses.length;

  const selectedCourse = useMemo(() => {
    return courses.find((course) => course.id === selectedCourseId) ?? null;
  }, [courses, selectedCourseId]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="bg-white border-b border-slate-200">
        <div className="flex flex-col gap-6 px-6 py-4 mx-auto lg:flex-row lg:items-center lg:justify-between max-w-7xl">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Teacher Dashboard</h1>
            <p className="max-w-2xl text-sm text-slate-500">
              Review student submissions by course, inspect assignment details, and
              download individual files, course ZIP exports, or CSV result summaries.
            </p>
          </div>

          <div className="px-4 py-2 text-sm font-medium text-blue-700 rounded-full bg-blue-50">
            Welcome, {data?.member.first_name ?? data?.member.upi ?? "Teacher"}.
          </div>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 px-3 mt-8 mb-8 md:grid-cols-2 xl:grid-cols-2">
        <StatCard icon={BookOpen} label="Current Active Courses" value={totalCourses} />
        <StatCard icon={Users} label="Total Submissions" value={totalSubmissions} />
      </section>

      <section className="p-6 mx-3 bg-white border shadow-sm rounded-2xl border-slate-200">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-500">Courses</h2>
            <p className="text-sm text-slate-400">
              Select a course to view submissions
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-6 text-sm text-slate-500">Loading courses...</div>
        ) : error ? (
          <div className="py-6 text-sm text-red-600">{error}</div>
        ) : courses.length === 0 ? (
          <div className="py-6 text-sm text-slate-500">No active courses found.</div>
        ) : (
          <div className="space-y-3">
            {courses.map((course) => {
              const active = course.id === selectedCourseId;

              return (
                <button
                  key={course.id}
                  type="button"
                  onClick={() => {
                    setSelectedCourseId(course.id);
                  }}
                  className={`w-full rounded-3xl border p-4 text-left transition ${
                    active
                      ? "border-slate-600 bg-slate-600 shadow-sm"
                      : "border-slate-200 bg-slate-100 hover:bg-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className={`text-sm font-medium ${active ? "text-sky-300" : "text-sky-500"}`}>
                        {course.course_code ?? "No course code"}
                      </p>

                      <h3
                        className={`mt-1 text-base font-semibold ${
                          active ? "text-white" : "text-slate-900"
                        }`}
                      >
                        {course.name ?? "Untitled Course"}
                      </h3>

                      <p className={`mt-1 text-xs ${active ? "text-slate-300" : "text-slate-400"}`}>
                        {course.start_date && course.end_date
                          ? `${course.start_date} - ${course.end_date}`
                          : "Active course"}
                      </p>
                    </div>

                    <div>
                        <a className={`inline-flex items-center justify-center gap-2 px-4 py-3 mr-2 text-xs font-medium transition rounded-2xl cursor-pointer ${
                            active
                              ? "bg-white/10 ring-1 ring-inset ring-white/10 hover:bg-white/15"
                              : "bg-white/10 ring-1 ring-inset ring-white/10 hover:bg-white/15"
                            }`}
                            onClick={() => handleZipDownload(course?.name ?? "")}
                            >
                            <FileSpreadsheet className="w-4 h-4" />
                            Zip Files
                        </a>
                        <a className={`inline-flex items-center justify-center gap-2 px-4 py-3 text-xs font-medium transition rounded-2xl cursor-pointer ${
                            active
                              ? "bg-sky-500 text-slate-950 hover:brightness-110"
                              : "bg-sky-500 text-slate-950 hover:brightness-110"
                            }`}
                            onClick={() => handleCSVDownload(course?.id)}
                            >
                            <FileSpreadsheet className="w-4 h-4" />
                            Assignment Results (CSV)
                        </a>
                    </div>
                    {/* <span
                      className={`px-3 py-1 text-xs rounded-full ${
                        active
                          ? "bg-white/10 text-slate-200"
                          : "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {course.submitted_students.length}
                    </span> */}
                  </div>

                  <div className={`flex items-center justify-between mt-4 text-xs ${
                    active ? "text-slate-300" : "text-slate-500"
                  }`}>
                    <span>{course.students.length} students</span>
                    <span>{course.submitted_students.length} submitted</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {selectedCourse && (
        <section className="p-6 mx-3 mt-6 mb-8 bg-white border shadow-sm rounded-2xl border-slate-200">
          <h2 className="text-lg font-semibold text-slate-700">
            Selected Course
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            {selectedCourse.course_code} — {selectedCourse.name}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {selectedCourse.students.length} students •{" "}
            {selectedCourse.submitted_students.length} submitted
          </p>
        </section>
      )}
    </div>
  );
}