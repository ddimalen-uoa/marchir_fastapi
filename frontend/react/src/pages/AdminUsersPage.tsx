import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, LoaderCircle, Pencil, RotateCcw, Search, X } from "lucide-react";
import { assignTeacherCourses, listAdminCourses, listAdminUsers, moveAdminUser, updateAdminUser } from "../api/adminUsersApi";
import type { AdminCourse, AdminUser, UserChanges } from "../api/adminUsersApi";

const inputClass = "w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";
const buttonClass = "inline-flex items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50";
const userName = (user: AdminUser) => [user.first_name, user.last_name].filter(Boolean).join(" ") || user.upi || user.email || `User ${user.id}`;

function UserEditor({ user, courses, onClose, onUpdated }: { user: AdminUser; courses: AdminCourse[]; onClose: () => void; onUpdated: () => Promise<void> }) {
  const [form, setForm] = useState<UserChanges>({ first_name: user.first_name, last_name: user.last_name, email: user.email, upi: user.upi, role: user.role === "teacher" ? "teacher" : "student", is_active: user.is_active });
  const [enrollments, setEnrollments] = useState(user.enrollments);
  const [savedRole, setSavedRole] = useState(user.role);
  const [assignedIds, setAssignedIds] = useState((user.teacher_courses ?? []).map((course) => course.id));
  const [savedAssignedIds, setSavedAssignedIds] = useState(assignedIds);
  const [sourceId, setSourceId] = useState(String(user.enrollments[0]?.id ?? ""));
  const [destination, setDestination] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const source = enrollments.find((item) => String(item.id) === sourceId);
  const destinations = courses.filter((course) => course.is_active && !enrollments.some((item) => item.course_id === course.id));

  async function saveDetails(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(null); setMessage(null);
    try {
      await updateAdminUser(user.id, { ...form, email: form.email?.trim() || null, upi: form.upi?.trim() || null });
      setSavedRole(form.role);
      if (form.role !== "teacher") { setAssignedIds([]); setSavedAssignedIds([]); }
      await onUpdated();
      setMessage("User details saved.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save user."); }
    finally { setSaving(false); }
  }

  async function saveAssignments() {
    setSaving(true); setError(null); setMessage(null);
    try {
      await assignTeacherCourses(user.id, assignedIds);
      setSavedAssignedIds(assignedIds);
      await onUpdated();
      setMessage("Teacher course assignments saved.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save assignments."); }
    finally { setSaving(false); }
  }

  async function moveCourse() {
    if (!destination || source?.has_submission) return;
    setSaving(true); setError(null); setMessage(null);
    try {
      await moveAdminUser(user.id, source?.id ?? null, Number(destination));
      const target = courses.find((course) => course.id === Number(destination))!;
      if (source) setEnrollments((items) => items.map((item) => item.id === source.id ? { ...item, course_id: target.id, course_name: target.name, course_code: target.course_code } : item));
      await onUpdated();
      setDestination("");
      setMessage(source ? "Course enrollment moved." : "User enrolled in course.");
      if (!source) onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not update enrollment."); }
    finally { setSaving(false); }
  }

  return (
    <Dialog.Root open onOpenChange={(open) => { if (!open && !saving) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-xl -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg bg-white p-6 shadow-xl" onEscapeKeyDown={(event) => { if (saving) event.preventDefault(); }} onPointerDownOutside={(event) => { if (saving) event.preventDefault(); }}>
          <div className="mb-5 flex items-start justify-between gap-4">
            <div className="min-w-0"><Dialog.Title className="text-lg font-semibold text-gray-900">Edit user</Dialog.Title><Dialog.Description className="mt-1 break-words text-sm text-gray-500">{userName(user)}</Dialog.Description></div>
            <Dialog.Close disabled={saving} className={buttonClass} title="Close" aria-label="Close"><X className="h-4 w-4" /></Dialog.Close>
          </div>
          {error && <p role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          {message && <p role="status" className="mb-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
          <form onSubmit={saveDetails} className="grid gap-4 sm:grid-cols-2">
            {(["first_name", "last_name", "email", "upi"] as const).map((key) => (
              <label key={key} className="space-y-1 text-sm font-medium text-gray-700">
                <span>{{ first_name: "First name", last_name: "Last name", email: "Email", upi: "UPI" }[key]}</span>
                <input className={inputClass} type={key === "email" ? "email" : "text"} value={form[key] ?? ""} maxLength={key === "upi" ? 20 : 100} disabled={saving} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
              </label>
            ))}
            <label className="space-y-1 text-sm font-medium text-gray-700"><span>User type</span><select className={inputClass} value={form.role} disabled={saving} onChange={(event) => setForm({ ...form, role: event.target.value as UserChanges["role"] })}><option value="student">Student</option><option value="teacher">Teacher</option></select></label>
            <div className="self-center"><label className="flex items-center gap-2 text-sm font-medium text-gray-700"><input type="checkbox" checked={form.is_active} disabled={saving} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} className="h-4 w-4 accent-blue-700" />Login enabled</label><p className="mt-1 text-xs text-gray-500">Disabling login also signs the user out.</p></div>
            <div className="sm:col-span-2"><button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50">{saving && <LoaderCircle className="h-4 w-4 animate-spin" />}Save details</button></div>
          </form>
          {savedRole === "teacher" ? <section className="mt-6 border-t border-gray-200 pt-5">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Teaching courses</h2>
            <fieldset disabled={saving} className="max-h-60 space-y-2 overflow-y-auto">
              <legend className="sr-only">Assigned teaching courses</legend>
              {courses.map((course) => <label key={course.id} className="flex items-start gap-3 rounded-md px-2 py-2 text-sm text-gray-700 hover:bg-gray-50">
                <input type="checkbox" className="mt-0.5 h-4 w-4 shrink-0 accent-blue-700" checked={assignedIds.includes(course.id)} disabled={!course.is_active && !savedAssignedIds.includes(course.id)} onChange={(event) => setAssignedIds((ids) => event.target.checked ? [...ids, course.id] : ids.filter((id) => id !== course.id))} />
                <span className="min-w-0 break-words">{course.name}{!course.is_active && <span className="ml-2 text-xs text-gray-500">Inactive</span>}</span>
              </label>)}
              {courses.length === 0 && <p className="text-sm text-gray-500">No courses available.</p>}
            </fieldset>
            <button type="button" onClick={saveAssignments} disabled={saving} className={`${buttonClass} mt-4`}>Save course assignments</button>
          </section> : <section className="mt-6 border-t border-gray-200 pt-5">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Course enrollment</h2>
            {enrollments.length > 0 && <label className="mb-3 block space-y-1 text-sm font-medium text-gray-700"><span>Current course</span><select className={inputClass} value={sourceId} disabled={saving} onChange={(event) => { setSourceId(event.target.value); setDestination(""); setMessage(null); }}>
              {enrollments.map((item) => <option key={item.id} value={item.id}>{item.course_name}{item.has_submission ? " (submitted)" : ""}</option>)}
            </select></label>}
            {source?.has_submission ? <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">This user has submitted an assignment for this course. This enrollment cannot be moved.</p> : <>
              <label className="block space-y-1 text-sm font-medium text-gray-700"><span>{source ? "Move to course" : "Enroll in course"}</span><select className={inputClass} value={destination} disabled={saving} onChange={(event) => setDestination(event.target.value)}><option value="">Select a course</option>{destinations.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}</select></label>
              {destinations.length === 0 && <p className="mt-2 text-sm text-gray-500">No other active courses are available.</p>}
              <button type="button" onClick={moveCourse} disabled={saving || !destination} className={`${buttonClass} mt-3`}>{source ? "Move enrollment" : "Enroll user"}</button>
            </>}
          </section>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [course, setCourse] = useState("");
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [submission, setSubmission] = useState("");
  const [sort, setSort] = useState("name");
  const [direction, setDirection] = useState("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  useEffect(() => { const timer = window.setTimeout(() => { setDebouncedSearch(search); setPage(1); }, 300); return () => window.clearTimeout(timer); }, [search]);
  const params = new URLSearchParams({ search: debouncedSearch, sort, direction, page: String(page), page_size: String(pageSize) });
  if (course === "none") params.set("unenrolled", "true"); else if (course) params.set("course_id", course);
  if (role) params.set("role", role);
  if (active) params.set("active", active);
  if (submission) params.set("submission", submission);
  const users = useQuery({ queryKey: ["admin-users", params.toString()], queryFn: () => listAdminUsers(params), retry: false });
  const courses = useQuery({ queryKey: ["admin-courses"], queryFn: listAdminCourses, retry: false });
  const totalPages = Math.max(1, Math.ceil((users.data?.total ?? 0) / pageSize));
  useEffect(() => { if (users.data && page > totalPages) setPage(totalPages); }, [users.data, page, totalPages]);

  function resetFilters() { setSearch(""); setDebouncedSearch(""); setCourse(""); setRole(""); setActive(""); setSubmission(""); setSort("name"); setDirection("asc"); setPage(1); }
  const selectFilter = (setter: (value: string) => void) => (event: ChangeEvent<HTMLSelectElement>) => { setter(event.target.value); setPage(1); };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-2xl font-semibold text-gray-900">Users</h1><p className="mt-1 text-sm text-gray-500">{users.data?.total ?? 0} users</p></div><button onClick={resetFilters} className={buttonClass}><RotateCcw className="h-4 w-4" />Reset filters</button></div>
      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>Search users</span><div className="relative"><Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" /><input type="search" value={search} maxLength={200} onChange={(event) => setSearch(event.target.value)} placeholder="Name, email or UPI" className={`${inputClass} pl-9`} /></div></label>
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>Course</span><select aria-label="Course" className={inputClass} value={course} onChange={selectFilter(setCourse)} disabled={courses.isPending || courses.isError}><option value="">All courses</option><option value="none">Not enrolled</option>{courses.data?.map((item) => <option key={item.id} value={item.id}>{item.name}{item.is_active ? "" : " (inactive)"}</option>)}</select></label>
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>User type</span><select className={inputClass} value={role} onChange={selectFilter(setRole)}><option value="">All types</option><option value="student">Student</option><option value="teacher">Teacher</option></select></label>
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>Login status</span><select className={inputClass} value={active} onChange={selectFilter(setActive)}><option value="">All statuses</option><option value="true">Enabled</option><option value="false">Deactivated</option></select></label>
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>Assignment submission</span><select className={inputClass} value={submission} onChange={selectFilter(setSubmission)}><option value="">All users</option><option value="yes">Has submitted</option><option value="no">Has not submitted</option></select></label>
        <label className="space-y-1 text-xs font-medium text-gray-600"><span>Sort by</span><select aria-label="Sort by" className={inputClass} value={sort} onChange={selectFilter(setSort)}><option value="name">Name</option><option value="email">Email</option><option value="role">User type</option><option value="course">Course</option><option value="created">Registration date</option></select></label>
        <div className="flex items-end"><button type="button" className={buttonClass} onClick={() => { setDirection(direction === "asc" ? "desc" : "asc"); setPage(1); }}>{direction === "asc" ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}{direction === "asc" ? "Ascending" : "Descending"}</button></div>
      </div>
      {courses.isError && <p role="alert" className="mb-4 text-sm text-red-700">Courses could not be loaded. <button className="underline" onClick={() => courses.refetch()}>Retry</button></p>}
      {users.isPending ? <div role="status" className="flex items-center justify-center gap-2 py-16 text-sm text-gray-500"><LoaderCircle className="h-5 w-5 animate-spin" />Loading users...</div> : users.isError ? <div role="alert" className="border-y border-red-200 bg-red-50 p-4 text-sm text-red-700">{users.error.message} <button className="underline" onClick={() => users.refetch()}>Retry</button></div> : <>
        <div className="relative overflow-x-auto border-y border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-xs font-semibold text-gray-600"><tr>{["User", "Type", "Courses", "Login", ""].map((label) => <th key={label} scope="col" className="px-4 py-3">{label || <span className="sr-only">Actions</span>}</th>)}</tr></thead>
            <tbody className="divide-y divide-gray-100">{users.data?.items.map((user) => <tr key={user.id} className="hover:bg-gray-50">
              <td className="min-w-52 max-w-xs px-4 py-4"><div className="break-words font-medium text-gray-900">{userName(user)}</div><div className="break-all text-xs text-gray-500">{user.email || "No email"}</div>{user.upi && <div className="mt-1 text-xs text-gray-500">{user.upi}</div>}</td>
              <td className="px-4 py-4 capitalize text-gray-700">{user.role || "Unassigned"}</td>
              <td className="min-w-48 max-w-sm px-4 py-4">{user.role === "teacher" ? ((user.teacher_courses ?? []).length ? user.teacher_courses.map((course) => <div key={course.id} className="mb-1 break-words text-gray-700">{course.name}</div>) : <span className="text-gray-400">No courses assigned</span>) : user.enrollments.length ? user.enrollments.map((item) => <div key={item.id} className="mb-1 break-words text-gray-700">{item.course_name}{item.has_submission && <span className="ml-2 text-xs font-medium text-amber-700">Submitted</span>}</div>) : <span className="text-gray-400">Not enrolled</span>}</td>
              <td className="px-4 py-4"><span className={`whitespace-nowrap text-xs font-medium ${user.is_active ? "text-emerald-700" : "text-red-700"}`}>{user.is_active ? "Enabled" : "Deactivated"}</span></td>
              <td className="px-4 py-4 text-right"><button type="button" disabled={!courses.data} onClick={() => setEditing(user)} className={buttonClass} title={`Edit ${userName(user)}`} aria-label={`Edit ${userName(user)}`}><Pencil className="h-4 w-4" /></button></td>
            </tr>)}</tbody>
          </table>
          {users.data?.items.length === 0 && <p className="px-4 py-14 text-center text-sm text-gray-500">No users match your filters.</p>}
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600">
          <label className="flex items-center gap-2">Per page<select value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPage(1); }} className="rounded-md border border-gray-300 bg-white px-2 py-1">{[20, 50, 100].map((size) => <option key={size}>{size}</option>)}</select></label>
          <div className="flex items-center gap-3"><span>Page {page} of {totalPages}</span><button className={buttonClass} disabled={page === 1} onClick={() => setPage(page - 1)} aria-label="Previous page" title="Previous page"><ChevronLeft className="h-4 w-4" /></button><button className={buttonClass} disabled={page >= totalPages} onClick={() => setPage(page + 1)} aria-label="Next page" title="Next page"><ChevronRight className="h-4 w-4" /></button></div>
        </div>
      </>}
      {editing && <UserEditor key={editing.id} user={editing} courses={courses.data ?? []} onClose={() => setEditing(null)} onUpdated={async () => { await queryClient.invalidateQueries({ queryKey: ["admin-users"] }); }} />}
    </main>
  );
}
