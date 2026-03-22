import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  CalendarDays,
  CirclePlus,
  UserPlus,
  LoaderCircle,
  // Power,
  Search,
  PauseCircle,
  // Users,
} from "lucide-react";
import { type CourseEnrolled } from "@/types/course";
import { getCoursesAndEnrollments, runAutoEnrollment, addNewCourse, updateCourse } from "../api/api";
import { useAuth } from "../features/auth/useAuth";
import { delay } from "@/features/utilities/delaysTimer";

type CourseFormState = {
  name: string;
  course_code: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  enrolled_students: number;
};

const fetchCourses = async (): Promise<CourseEnrolled[]> => {
  const courses = await getCoursesAndEnrollments();

  await delay(1000);
  
  return courses;
};

const emptyFormState: CourseFormState = {
  name: "",
  course_code: "",
  start_date: "",
  end_date: "",
  is_active: true,
  enrolled_students: 0,
};

const formatDate = (date: string) => {
  if (!date) return "—";

  return new Date(date).toLocaleDateString("en-NZ", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

const StatCard = ({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) => {
  return (
    <div className="p-5 bg-white border shadow-sm rounded-3xl border-slate-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
            {value}
          </p>
        </div>

        <div className="p-3 rounded-2xl bg-slate-100 text-slate-700">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};

const FullPageLoader = ({ isVisible, loaderMessage }: { isVisible: boolean, loaderMessage: string }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/30 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3 px-8 py-6 border shadow-xl rounded-3xl border-slate-200 bg-white/90">
        <LoaderCircle className="w-8 h-8 animate-spin text-slate-700" />
        <p className="text-sm font-medium text-slate-600">{loaderMessage}</p>
      </div>
    </div>
  );
};

export default function AdminDashboard() {
  const [courses, setCourses] = useState<CourseEnrolled[]>([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [activeLoaderMessage, setActiveLoaderMessage] = useState("Loading courses...");
  const [showPageLoader, setShowPageLoader] = useState(false);
  const [coursesError, setCoursesError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [showAddCourseForm, setShowAddCourseForm] = useState(false);
  const [isEditingCourse, setIsEditingCourse] = useState(false);
  const [newCourse, setNewCourse] = useState<CourseFormState>(emptyFormState);
  const [editCourse, setEditCourse] = useState<CourseFormState>(emptyFormState);
  const [currentPage, setCurrentPage] = useState(1);
  const { data: memberData } = useAuth();

  const coursesPerPage = 5;

  const autoEnrollStudents = async () => {
    let isMounted = true;
    
    setActiveLoaderMessage("Auto enrollment is now in progress...");
    setShowPageLoader(true);
    setCoursesError(null);
    await runAutoEnrollment();
    try {
      setIsLoadingCourses(true);
      setCoursesError(null);
      
      const data = await fetchCourses();

      if (!isMounted) return;

      setCourses(data);
      setSelectedCourseId((prev) => prev || data[0]?.id || "");
    } catch (error) {
      if (!isMounted) return;
      
        console.error("Failed to load courses", error);
        setCoursesError("Failed to load courses.");      
    } finally {
        if (isMounted) {
          setIsLoadingCourses(false);
          setShowPageLoader(false);
        }
    }
    
    return true;
  }

  useEffect(() => {
    let isMounted = true;

    const loadCourses = async () => {
      try {
        setActiveLoaderMessage("Loading courses...");
        setIsLoadingCourses(true);
        setShowPageLoader(true);
        setCoursesError(null);

        const data = await fetchCourses();

        if (!isMounted) return;

        setCourses(data);
        setSelectedCourseId((prev) => prev || data[0]?.id || "");
      } catch (error) {
        if (!isMounted) return;

        console.error("Failed to load courses", error);
        setCoursesError("Failed to load courses.");
      } finally {
        if (isMounted) {
          setIsLoadingCourses(false);
          setShowPageLoader(false);
        }
      }
    };

    loadCourses();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredCourses = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return courses;

    return courses.filter((course) => {
      return (
        course.name.toLowerCase().includes(term) ||
        course.course_code.toLowerCase().includes(term)
      );
    });
  }, [courses, searchTerm]);

  const totalPages = Math.max(1, Math.ceil(filteredCourses.length / coursesPerPage));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  useEffect(() => {
    if (filteredCourses.length === 0) {
      setSelectedCourseId("");
      setIsEditingCourse(false);
      return;
    }

    const stillExists = filteredCourses.some((course) => course.id === selectedCourseId);

    if (!stillExists) {
      setSelectedCourseId(filteredCourses[0].id);
      setIsEditingCourse(false);
    }
  }, [filteredCourses, selectedCourseId]);

  const paginatedCourses = useMemo(() => {
    const startIndex = (currentPage - 1) * coursesPerPage;
    return filteredCourses.slice(startIndex, startIndex + coursesPerPage);
  }, [filteredCourses, currentPage]);

  const selectedCourse = useMemo(() => {
    return courses.find((course) => course.id === selectedCourseId) ?? null;
  }, [courses, selectedCourseId]);

  const activeCoursesCount = useMemo(() => {
    return courses.filter((course) => course.is_active).length;
  }, [courses]);

  const inactiveCoursesCount = courses.length - activeCoursesCount;

  // const totalEnrolledStudents = useMemo(() => {
  //   return courses.reduce((sum, course) => sum + course.enrolled_students, 0);
  // }, [courses]);

  const resetAddForm = () => {
    setNewCourse(emptyFormState);
    setShowAddCourseForm(false);
  };
  
  const waitForNextPaint = () =>
  new Promise<void>((resolve) => {
    requestAnimationFrame(() => resolve());
  });

  const handleAddCourse = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (
      !newCourse.name.trim() ||
      !newCourse.course_code.trim() ||
      !newCourse.start_date ||
      !newCourse.end_date
    ) {
      return;
    }

    const formData = new FormData();
    formData.append("name", newCourse.name.trim());
    formData.append("course_code", newCourse.course_code.trim());
    formData.append("start_date", newCourse.start_date);
    formData.append("end_date", newCourse.end_date);
    formData.append("is_active", newCourse.is_active ? "true" : "false");

    try {
      setActiveLoaderMessage("Adding new course...");
      setShowPageLoader(true);

      await waitForNextPaint();

      const courseData = await addNewCourse(formData);

      await delay(1000);

      const createdCourse: CourseEnrolled = {
        id: courseData.course.id,
        name: newCourse.name.trim(),
        course_code: newCourse.course_code.trim(),
        start_date: newCourse.start_date,
        end_date: newCourse.end_date,
        is_active: newCourse.is_active,
        enrolled_students: Number(newCourse.enrolled_students) || 0,
      };

      setCourses((prev) => [createdCourse, ...prev]);
      setSelectedCourseId(createdCourse.id);
      setCurrentPage(1);
      setIsEditingCourse(false);
      resetAddForm();
    } finally {
      setShowPageLoader(false);
    }
  };

  const startEditingCourse = () => {
    if (!selectedCourse) return;

    setEditCourse({
      name: selectedCourse.name,
      course_code: selectedCourse.course_code,
      start_date: selectedCourse.start_date,
      end_date: selectedCourse.end_date,
      is_active: selectedCourse.is_active,
      enrolled_students: selectedCourse.enrolled_students,
    });
    setIsEditingCourse(true);
    setShowAddCourseForm(false);
  };

  const handleUpdateCourse = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData();

    if (
      !selectedCourse ||
      !editCourse.name.trim() ||
      !editCourse.course_code.trim() ||
      !editCourse.start_date ||
      !editCourse.end_date
    ) {
      return;
    }

    formData.append("name", editCourse.name.trim());
    formData.append("course_code", editCourse.course_code.trim());
    formData.append("start_date", editCourse.start_date);
    formData.append("end_date", editCourse.end_date);
    formData.append("is_active", editCourse.is_active ? "true" : "false");

    try {
      setActiveLoaderMessage("Updating course...");
      setShowPageLoader(true);    

      await waitForNextPaint();

      await updateCourse(formData, selectedCourse.id.toString());

      await delay(1000);

      setIsLoadingCourses(false);

      setCourses((prev) =>
        prev.map((course) =>
          course.id === selectedCourse.id
            ? {
                ...course,
                name: editCourse.name.trim(),
                course_code: editCourse.course_code.trim(),
                start_date: editCourse.start_date,
                end_date: editCourse.end_date,
                is_active: editCourse.is_active,
                enrolled_students: Number(editCourse.enrolled_students) || 0,
              }
            : course,
        ),
      );
    } finally {
      setShowPageLoader(false);
    }
  };

  const handleSelectCourse = (courseId: string) => {
    setSelectedCourseId(courseId);
    setIsEditingCourse(false);
  };

  const handlePreviousPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
    setIsEditingCourse(false);
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
    setIsEditingCourse(false);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <FullPageLoader isVisible={showPageLoader} loaderMessage={activeLoaderMessage} />

      <div className={showPageLoader ? "pointer-events-none blur-[2px]" : ""}>
        <header className="bg-white border-b border-slate-200">
          <div className="flex flex-col gap-6 px-6 py-5 mx-auto max-w-7xl lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Admin Dashboard</h1>
              <p className="mt-1 text-sm text-slate-600">
                Manage available courses, create new offerings, and review course details.
              </p>
            </div>

            <div className="px-4 py-2 text-sm font-medium text-blue-700 rounded-full bg-blue-50">
              Welcome, {memberData?.member.first_name ?? memberData?.member.upi ?? "Admin"}.
            </div>
          </div>
        </header>

        <main className="px-6 py-8 mx-auto max-w-7xl">
          <section className="grid gap-4 md:grid-cols-3">
            <StatCard icon={BookOpen} label="Total Courses" value={courses.length} />
            <StatCard icon={PauseCircle} label="Active Courses" value={activeCoursesCount} />
            <StatCard icon={CalendarDays} label="Inactive Courses" value={inactiveCoursesCount} />
            {/* <StatCard icon={Users} label="Total Enrolled" value={totalEnrolledStudents} /> */}
          </section>

          {showAddCourseForm && (
            <section className="p-6 mt-8 bg-white border shadow-sm rounded-3xl border-slate-200">
              <div className="mb-6">
                <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                  Add New Course
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  This currently updates local state, but you can replace it with your create-course API request later.
                </p>
              </div>

              <form onSubmit={(event) => handleAddCourse(event)} className="grid gap-5 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">Course Name</span>
                  <input
                    type="text"
                    value={newCourse.name}
                    onChange={(e) => setNewCourse((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter course name"
                    className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">Course Code</span>
                  <input
                    type="text"
                    value={newCourse.course_code}
                    onChange={(e) =>
                      setNewCourse((prev) => ({ ...prev, course_code: e.target.value }))
                    }
                    placeholder="Enter course code"
                    className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">Start Date</span>
                  <input
                    type="date"
                    value={newCourse.start_date}
                    onChange={(e) =>
                      setNewCourse((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                    className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">End Date</span>
                  <input
                    type="date"
                    value={newCourse.end_date}
                    onChange={(e) => setNewCourse((prev) => ({ ...prev, end_date: e.target.value }))}
                    className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                  />
                </label>

                {/* <label className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-slate-700">Enrolled Students</span>
                  <input
                    type="number"
                    min="0"
                    value={newCourse.enrolled_students}
                    onChange={(e) =>
                      setNewCourse((prev) => ({
                        ...prev,
                        enrolled_students: Number(e.target.value),
                      }))
                    }
                    placeholder="Enter number of enrolled students"
                    className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                  />
                </label> */}

                <label className="flex items-center gap-3 px-4 py-3 border rounded-2xl border-slate-200 bg-slate-50 md:col-span-2">
                  <input
                    type="checkbox"
                    checked={newCourse.is_active}
                    onChange={(e) => setNewCourse((prev) => ({ ...prev, is_active: e.target.checked }))}
                    className="w-4 h-4 rounded border-slate-300"
                  />
                  <span className="text-sm font-medium text-slate-700">Course is active</span>
                </label>

                <div className="flex flex-wrap gap-3 md:col-span-2">
                  <button
                    type="submit"
                    className="px-5 py-3 text-sm font-medium text-white transition rounded-2xl bg-slate-900 hover:bg-slate-800"
                  >
                    Save Course
                  </button>
                  <button
                    type="button"
                    onClick={resetAddForm}
                    className="px-5 py-3 text-sm font-medium transition bg-white border rounded-2xl border-slate-300 text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </section>
          )}

          <section className="mt-8 grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
            <aside className="p-5 bg-white border shadow-sm rounded-3xl border-slate-200">
              <div className="mb-4">
                <div className="flex items-center justify-between mb-6">
                      <button
                        type="button"
                        onClick={() => autoEnrollStudents()}
                        className="inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-white transition bg-green-500 rounded-2xl hover:bg-green-400"
                      >
                        <UserPlus className="w-4 h-4" />
                        Auto Enroll Students
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setShowAddCourseForm((prev) => !prev);
                          setIsEditingCourse(false);
                        }}
                        className="inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-white transition bg-blue-500 rounded-2xl hover:bg-blue-400"
                      >
                        <CirclePlus className="w-4 h-4" />
                        Add New Course
                      </button>
                </div>              
                <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                  Available Courses
                </h2>
                <p className="text-sm text-slate-500">
                  Select a course to view or edit its details.
                </p>
              </div>

              <div className="relative mb-4">
                <Search className="absolute w-4 h-4 -translate-y-1/2 pointer-events-none left-3 top-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder="Search courses"
                  className="w-full py-3 pl-10 pr-4 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                />
              </div>

              {isLoadingCourses ? (
                <div className="px-4 py-8 text-sm text-center border border-dashed rounded-2xl border-slate-300 text-slate-500">
                  Loading courses...
                </div>
              ) : coursesError ? (
                <div className="px-4 py-8 text-sm text-center border border-dashed rounded-2xl border-rose-300 bg-rose-50 text-rose-600">
                  {coursesError}
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    {paginatedCourses.length > 0 ? (
                      paginatedCourses.map((course) => {
                        const isSelected = selectedCourseId === course.id;

                        return (
                          <button
                            key={course.id}
                            type="button"
                            onClick={() => handleSelectCourse(course.id)}
                            className={`w-full rounded-2xl border p-4 text-left transition ${
                              isSelected
                                ? "border-slate-900 bg-slate-900 text-white"
                                : "border-slate-200 bg-slate-50 text-slate-900 hover:bg-slate-100"
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-sm font-semibold tracking-tight">{course.name}</p>
                                <p
                                  className={`mt-1 text-xs ${
                                    isSelected ? "text-slate-300" : "text-slate-500"
                                  }`}
                                >
                                  {course.course_code}
                                </p>
                                <p
                                  className={`mt-2 text-xs ${
                                    isSelected ? "text-slate-300" : "text-slate-500"
                                  }`}
                                >
                                  {course.enrolled_students} enrolled students
                                </p>
                              </div>

                              <span
                                className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                                  isSelected
                                    ? "bg-white/15 text-white"
                                    : course.is_active
                                      ? "bg-emerald-100 text-emerald-700"
                                      : "bg-slate-200 text-slate-600"
                                }`}
                              >
                                {course.is_active ? "Active" : "Inactive"}
                              </span>
                            </div>
                          </button>
                        );
                      })
                    ) : (
                      <div className="px-4 py-8 text-sm text-center border border-dashed rounded-2xl border-slate-300 text-slate-500">
                        No courses found.
                      </div>
                    )}
                  </div>

                  {filteredCourses.length > 0 && (
                    <div className="flex items-center justify-between gap-3 pt-4 mt-4 border-t border-slate-200">
                      <p className="text-xs text-slate-500">
                        Page {currentPage} of {totalPages}
                      </p>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={handlePreviousPage}
                          disabled={currentPage === 1}
                          className="px-3 py-2 text-sm font-medium transition bg-white border rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          onClick={handleNextPage}
                          disabled={currentPage === totalPages}
                          className="px-3 py-2 text-sm font-medium transition bg-white border rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </aside>

            <section className="p-6 bg-white border shadow-sm rounded-3xl border-slate-200">
              {isLoadingCourses ? (
                <div className="flex min-h-[320px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 text-center text-sm text-slate-500">
                  Loading course details...
                </div>
              ) : selectedCourse ? (
                <>
                  <div className="flex flex-col gap-4 pb-5 border-b border-slate-200 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-500">Course Details</p>
                      <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
                        {selectedCourse.name}
                      </h2>
                      <p className="mt-2 text-sm text-slate-600">
                        Review the selected course information below.
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className={`inline-flex w-fit rounded-full px-3 py-1 text-xs font-semibold ${
                          selectedCourse.is_active
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {selectedCourse.is_active ? "Currently Active" : "Currently Inactive"}
                      </span>

                      <button
                        type="button"
                        onClick={startEditingCourse}
                        className="px-4 py-2 text-sm font-medium transition bg-white border rounded-2xl border-slate-300 text-slate-700 hover:bg-slate-50"
                      >
                        Edit Course
                      </button>
                    </div>
                  </div>

                  {isEditingCourse ? (
                    <form onSubmit={(event) => handleUpdateCourse(event)} className="grid gap-5 mt-6 md:grid-cols-2">
                      <label className="space-y-2">
                        <span className="text-sm font-medium text-slate-700">Course Name</span>
                        <input
                          type="text"
                          value={editCourse.name}
                          onChange={(e) => setEditCourse((prev) => ({ ...prev, name: e.target.value }))}
                          className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                        />
                      </label>

                      <label className="space-y-2">
                        <span className="text-sm font-medium text-slate-700">Course Code</span>
                        <input
                          type="text"
                          value={editCourse.course_code}
                          onChange={(e) =>
                            setEditCourse((prev) => ({ ...prev, course_code: e.target.value }))
                          }
                          className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                        />
                      </label>

                      <label className="space-y-2">
                        <span className="text-sm font-medium text-slate-700">Start Date</span>
                        <input
                          type="date"
                          value={editCourse.start_date}
                          onChange={(e) =>
                            setEditCourse((prev) => ({ ...prev, start_date: e.target.value }))
                          }
                          className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                        />
                      </label>

                      <label className="space-y-2">
                        <span className="text-sm font-medium text-slate-700">End Date</span>
                        <input
                          type="date"
                          value={editCourse.end_date}
                          onChange={(e) => setEditCourse((prev) => ({ ...prev, end_date: e.target.value }))}
                          className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                        />
                      </label>

                      {/* <label className="space-y-2">
                        <span className="text-sm font-medium text-slate-700">Enrolled Students</span>
                        <input
                          type="number"
                          min="0"
                          value={editCourse.enrolled_students}
                          onChange={(e) =>
                            setEditCourse((prev) => ({
                              ...prev,
                              enrolled_students: Number(e.target.value),
                            }))
                          }
                          className="w-full px-4 py-3 text-sm transition bg-white border outline-none rounded-2xl border-slate-300 focus:border-slate-400"
                        />
                      </label> */}

                      <label className="flex items-center gap-3 px-4 py-3 border rounded-2xl border-slate-200 bg-slate-50">
                        <input
                          type="checkbox"
                          checked={editCourse.is_active}
                          onChange={(e) =>
                            setEditCourse((prev) => ({
                              ...prev,
                              is_active: e.target.checked,
                            }))
                          }
                          className="w-4 h-4 rounded border-slate-300"
                        />
                        <span className="text-sm font-medium text-slate-700">Course is active</span>
                      </label>

                      <div className="flex flex-wrap gap-3 md:col-span-2">
                        <button
                          type="submit"
                          className="px-5 py-3 text-sm font-medium text-white transition rounded-2xl bg-slate-900 hover:bg-slate-800"
                        >
                          Update Course
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsEditingCourse(false)}
                          className="px-5 py-3 text-sm font-medium transition bg-white border rounded-2xl border-slate-300 text-slate-700 hover:bg-slate-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="grid gap-4 mt-6 md:grid-cols-2">
                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          Course Name
                        </p>
                        <p className="mt-2 text-base font-medium text-slate-900">
                          {selectedCourse.name}
                        </p>
                      </div>

                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          Course Code
                        </p>
                        <p className="mt-2 text-base font-medium text-slate-900">
                          {selectedCourse.course_code}
                        </p>
                      </div>

                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          Start Date
                        </p>
                        <p className="mt-2 text-base font-medium text-slate-900">
                          {formatDate(selectedCourse.start_date)}
                        </p>
                      </div>

                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          End Date
                        </p>
                        <p className="mt-2 text-base font-medium text-slate-900">
                          {formatDate(selectedCourse.end_date)}
                        </p>
                      </div>

                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          Enrolled Students
                        </p>
                        <p className="mt-2 text-base font-medium text-slate-900">
                          {selectedCourse.enrolled_students}
                        </p>
                      </div>

                      <div className="p-4 border rounded-2xl border-slate-200 bg-slate-50">
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                          Active Status
                        </p>
                        <div className="flex items-center gap-3 mt-2">
                          <div
                            className={`h-3 w-3 rounded-full ${
                              selectedCourse.is_active ? "bg-emerald-500" : "bg-slate-400"
                            }`}
                          />
                          <p className="text-base font-medium text-slate-900">
                            {selectedCourse.is_active ? "Active" : "Inactive"}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex min-h-[320px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 text-center text-sm text-slate-500">
                  No course selected.
                </div>
              )}
            </section>
          </section>
        </main>
      </div>
    </div>
  );
}
