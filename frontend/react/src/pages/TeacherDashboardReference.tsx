import React, { useMemo, useState } from "react";
import {
  BookOpen,
  Download,
  FileDown,
  FileSpreadsheet,
  Search,
  Users,
  CheckCircle2,
  Clock3,
  Eye,
} from "lucide-react";


type SubmissionStatus = "Submitted" | "Late" | "Pending Review";
type ValidationResult = "Successful" | "Warnings" | "Failed";

type Submission = {
  id: string;
  studentName: string;
  studentId: string;
  email: string;
  submittedAt: string;
  fileName: string;
  fileSize: string;
  status: SubmissionStatus;
  validationResult: ValidationResult;
  score: string;
  downloadUrl: string;
  notes: string[];
};

type Course = {
  id: string;
  code: string;
  title: string;
  term: string;
  totalStudents: number;
  submissions: Submission[];
};

const courses: Course[] = [
  {
    id: "course-1",
    code: "SOFTENG 302",
    title: "Web Application Development",
    term: "Semester 1, 2026",
    totalStudents: 84,
    submissions: [
      {
        id: "sub-1",
        studentName: "Ava Thompson",
        studentId: "12003421",
        email: "ava.thompson@university.edu",
        submittedAt: "18 Mar 2026, 9:18 AM",
        fileName: "ava-thompson-assignment-2.zip",
        fileSize: "4.2 MB",
        status: "Submitted",
        validationResult: "Successful",
        score: "Pending",
        downloadUrl: "#",
        notes: [
          "HTML structure validated successfully.",
          "Required selectors were detected.",
          "Ready for manual marking.",
        ],
      },
      {
        id: "sub-2",
        studentName: "Noah Williams",
        studentId: "12004519",
        email: "noah.williams@university.edu",
        submittedAt: "18 Mar 2026, 8:53 AM",
        fileName: "noah-williams-assignment-2.zip",
        fileSize: "3.7 MB",
        status: "Pending Review",
        validationResult: "Warnings",
        score: "Pending",
        downloadUrl: "#",
        notes: [
          "One optional selector was missing.",
          "Submission can still be reviewed manually.",
        ],
      },
      {
        id: "sub-3",
        studentName: "Isla Chen",
        studentId: "12007843",
        email: "isla.chen@university.edu",
        submittedAt: "17 Mar 2026, 10:44 PM",
        fileName: "isla-chen-assignment-2.zip",
        fileSize: "5.1 MB",
        status: "Late",
        validationResult: "Successful",
        score: "78 / 100",
        downloadUrl: "#",
        notes: [
          "Submission was received after the deadline.",
          "Validation passed.",
          "Marked and released.",
        ],
      },
    ],
  },
  {
    id: "course-2",
    code: "COMPSCI 335",
    title: "Rich Internet Applications",
    term: "Semester 1, 2026",
    totalStudents: 56,
    submissions: [
      {
        id: "sub-4",
        studentName: "Luca Patel",
        studentId: "12008123",
        email: "luca.patel@university.edu",
        submittedAt: "18 Mar 2026, 7:41 AM",
        fileName: "luca-patel-project.zip",
        fileSize: "6.0 MB",
        status: "Submitted",
        validationResult: "Successful",
        score: "Pending",
        downloadUrl: "#",
        notes: ["All checks passed successfully."],
      },
      {
        id: "sub-5",
        studentName: "Mia Roberts",
        studentId: "12009994",
        email: "mia.roberts@university.edu",
        submittedAt: "17 Mar 2026, 11:02 PM",
        fileName: "mia-roberts-project.zip",
        fileSize: "4.8 MB",
        status: "Pending Review",
        validationResult: "Failed",
        score: "Pending",
        downloadUrl: "#",
        notes: [
          "Main entry file was not found.",
          "Please inspect the ZIP contents manually.",
        ],
      },
    ],
  },
  {
    id: "course-3",
    code: "INFOSYS 222",
    title: "Data and Information Management",
    term: "Semester 1, 2026",
    totalStudents: 102,
    submissions: [
      {
        id: "sub-6",
        studentName: "Ethan Walker",
        studentId: "12004555",
        email: "ethan.walker@university.edu",
        submittedAt: "18 Mar 2026, 9:05 AM",
        fileName: "ethan-walker-assignment.zip",
        fileSize: "3.3 MB",
        status: "Submitted",
        validationResult: "Successful",
        score: "Pending",
        downloadUrl: "#",
        notes: ["Ready for marking."],
      },
    ],
  },
];

function badgeClasses(value: string) {
  switch (value) {
    case "Submitted":
    case "Successful":
      return "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-400/30";
    case "Late":
    case "Warnings":
    case "Pending Review":
      return "bg-amber-500/15 text-amber-300 ring-1 ring-inset ring-amber-400/30";
    case "Failed":
      return "bg-rose-500/15 text-rose-300 ring-1 ring-inset ring-rose-400/30";
    default:
      return "bg-white/10 text-slate-200 ring-1 ring-inset ring-white/10";
  }
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) {
  return (
    <div className="p-5 border shadow-2xl rounded-3xl border-white/10 bg-white/5 shadow-black/20 backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
        </div>
        <div className="p-3 rounded-2xl bg-white/10 text-slate-200">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export default function TeacherDashboardReference() {
  const [selectedCourseId, setSelectedCourseId] = useState<string>(courses[0]?.id ?? "");
  const [selectedStudentId, setSelectedStudentId] = useState<string>(
    courses[0]?.submissions[0]?.id ?? "",
  );
  const [search, setSearch] = useState("");

  const selectedCourse = useMemo(
    () => courses.find((course) => course.id === selectedCourseId) ?? courses[0],
    [selectedCourseId],
  );

  const filteredStudents = useMemo(() => {
    if (!selectedCourse) return [];

    const query = search.trim().toLowerCase();
    if (!query) return selectedCourse.submissions;

    return selectedCourse.submissions.filter((submission) => {
      return (
        submission.studentName.toLowerCase().includes(query) ||
        submission.studentId.toLowerCase().includes(query) ||
        submission.email.toLowerCase().includes(query) ||
        submission.fileName.toLowerCase().includes(query)
      );
    });
  }, [search, selectedCourse]);

  const selectedSubmission = useMemo(() => {
    const fromFiltered = filteredStudents.find((submission) => submission.id === selectedStudentId);
    if (fromFiltered) return fromFiltered;
    return filteredStudents[0] ?? selectedCourse?.submissions[0];
  }, [filteredStudents, selectedCourse, selectedStudentId]);

  const totalSubmissions = courses.reduce((sum, course) => sum + course.submissions.length, 0);
  const totalCourses = courses.length;
  const successfulSubmissions = courses.reduce(
    (sum, course) =>
      sum + course.submissions.filter((submission) => submission.validationResult === "Successful").length,
    0,
  );
  const pendingReviews = courses.reduce(
    (sum, course) =>
      sum + course.submissions.filter((submission) => submission.status === "Pending Review").length,
    0,
  );

  return (
    <div className="min-h-screen text-white bg-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(168,85,247,0.14),_transparent_30%)]" />

      <div className="relative px-4 py-8 mx-auto max-w-7xl sm:px-6 lg:px-8">
        <header className="mb-8 rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur-md">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-sky-300/80">
                Teacher Portal
              </p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Teacher Dashboard
              </h1>
              <p className="max-w-2xl mt-3 text-sm leading-6 text-slate-300 sm:text-base">
                Review student submissions by course, inspect assignment details, and download
                individual files, course ZIP exports, or CSV result summaries.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <a
                href="#"
                className="inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-white transition rounded-2xl bg-white/10 ring-1 ring-inset ring-white/10 hover:bg-white/15"
              >
                <FileDown className="w-4 h-4" />
                Download Course ZIP
              </a>
              <a
                href="#"
                className="inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition rounded-2xl bg-sky-500 text-slate-950 hover:brightness-110"
              >
                <FileSpreadsheet className="w-4 h-4" />
                Export Results CSV
              </a>
            </div>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-4 mb-8 md:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={BookOpen} label="Current Courses" value={totalCourses} />
          <StatCard icon={Users} label="Total Submissions" value={totalSubmissions} />
          <StatCard icon={CheckCircle2} label="Successful Validations" value={successfulSubmissions} />
          <StatCard icon={Clock3} label="Pending Review" value={pendingReviews} />
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-[320px_360px_minmax(0,1fr)]">
          <aside className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur-md">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white">Courses</h2>
                <p className="text-sm text-slate-400">Select a course to view submissions</p>
              </div>
            </div>

            <div className="space-y-3">
              {courses.map((course) => {
                const active = course.id === selectedCourseId;
                return (
                  <button
                    key={course.id}
                    type="button"
                    onClick={() => {
                      setSelectedCourseId(course.id);
                      setSelectedStudentId(course.submissions[0]?.id ?? "");
                      setSearch("");
                    }}
                    className={`w-full rounded-3xl border p-4 text-left transition ${
                      active
                        ? "border-sky-400/40 bg-sky-500/10 shadow-lg shadow-sky-950/30"
                        : "border-white/10 bg-white/5 hover:bg-white/10"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-medium text-sky-300">{course.code}</p>
                        <h3 className="mt-1 text-base font-semibold text-white">{course.title}</h3>
                        <p className="mt-1 text-xs text-slate-400">{course.term}</p>
                      </div>
                      <span className="px-3 py-1 text-xs rounded-full bg-white/10 text-slate-200">
                        {course.submissions.length}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-4 text-xs text-slate-400">
                      <span>{course.totalStudents} students</span>
                      <span>{course.submissions.length} submitted</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </aside>

          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur-md">
            <div className="flex flex-col gap-4 mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white">Student Submissions</h2>
                <p className="text-sm text-slate-400">
                  {selectedCourse?.code} · {selectedCourse?.title}
                </p>
              </div>

              <div className="relative">
                <Search className="absolute w-4 h-4 -translate-y-1/2 pointer-events-none left-4 top-1/2 text-slate-500" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name, ID, email, or file"
                  className="w-full py-3 pr-4 text-sm text-white border outline-none rounded-2xl border-white/10 bg-slate-950/60 pl-11 ring-0 placeholder:text-slate-500 focus:border-sky-400/40"
                />
              </div>
            </div>

            <div className="space-y-3">
              {filteredStudents.length > 0 ? (
                filteredStudents.map((submission) => {
                  const active = selectedSubmission?.id === submission.id;
                  return (
                    <button
                      key={submission.id}
                      type="button"
                      onClick={() => setSelectedStudentId(submission.id)}
                      className={`w-full rounded-3xl border p-4 text-left transition ${
                        active
                          ? "border-sky-400/40 bg-sky-500/10"
                          : "border-white/10 bg-white/5 hover:bg-white/10"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="text-sm font-semibold text-white">{submission.studentName}</h3>
                          <p className="mt-1 text-xs text-slate-400">
                            {submission.studentId} · {submission.email}
                          </p>
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${badgeClasses(submission.status)}`}>
                          {submission.status}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-4 mt-3 text-xs text-slate-400">
                        <span className="truncate">{submission.fileName}</span>
                        <span>{submission.submittedAt}</span>
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="px-4 py-10 text-sm text-center border border-dashed rounded-3xl border-white/10 bg-slate-950/40 text-slate-400">
                  No submissions matched your search.
                </div>
              )}
            </div>
          </section>

          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur-md">
            {selectedSubmission ? (
              <>
                <div className="flex flex-col gap-4 pb-5 border-b border-white/10 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-sky-300">Submission Details</p>
                    <h2 className="mt-1 text-2xl font-semibold text-white">
                      {selectedSubmission.studentName}
                    </h2>
                    <p className="mt-2 text-sm text-slate-400">
                      {selectedSubmission.studentId} · {selectedSubmission.email}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded-full px-3 py-1.5 text-xs font-medium ${badgeClasses(selectedSubmission.status)}`}>
                      {selectedSubmission.status}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1.5 text-xs font-medium ${badgeClasses(
                        selectedSubmission.validationResult,
                      )}`}
                    >
                      {selectedSubmission.validationResult}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 py-5 sm:grid-cols-2">
                  <div className="p-4 border rounded-3xl border-white/10 bg-slate-950/50">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Submitted at</p>
                    <p className="mt-2 text-sm font-medium text-white">{selectedSubmission.submittedAt}</p>
                  </div>
                  <div className="p-4 border rounded-3xl border-white/10 bg-slate-950/50">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Score</p>
                    <p className="mt-2 text-sm font-medium text-white">{selectedSubmission.score}</p>
                  </div>
                  <div className="p-4 border rounded-3xl border-white/10 bg-slate-950/50">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">File name</p>
                    <p className="mt-2 text-sm font-medium text-white break-all">{selectedSubmission.fileName}</p>
                  </div>
                  <div className="p-4 border rounded-3xl border-white/10 bg-slate-950/50">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">File size</p>
                    <p className="mt-2 text-sm font-medium text-white">{selectedSubmission.fileSize}</p>
                  </div>
                </div>

                <div className="p-4 border rounded-3xl border-white/10 bg-slate-950/50">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-slate-400" />
                    <h3 className="text-sm font-semibold text-white">Submission Results</h3>
                  </div>

                  <ul className="mt-4 space-y-3">
                    {selectedSubmission.notes.map((note, index) => (
                      <li
                        key={`${selectedSubmission.id}-note-${index}`}
                        className="px-4 py-3 text-sm border rounded-2xl border-white/10 bg-white/5 text-slate-300"
                      >
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 gap-3 mt-5 sm:grid-cols-2">
                  <a
                    href={selectedSubmission.downloadUrl}
                    className="inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold transition rounded-2xl bg-sky-500 text-slate-950 hover:brightness-110"
                  >
                    <Download className="w-4 h-4" />
                    Download Assignment
                  </a>
                  <a
                    href="#"
                    className="inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white transition rounded-2xl bg-white/10 ring-1 ring-inset ring-white/10 hover:bg-white/15"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    Download Result CSV
                  </a>
                </div>
              </>
            ) : (
              <div className="flex h-full min-h-[420px] items-center justify-center rounded-3xl border border-dashed border-white/10 bg-slate-950/40 p-8 text-center text-sm text-slate-400">
                Select a student submission to view the details.
              </div>
            )}
          </section>
        </section>
      </div>
    </div>
  );
}
