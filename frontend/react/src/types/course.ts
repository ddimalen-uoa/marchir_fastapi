export type Student = {
  member_id: number;
  upi: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
};

export type Submission = {
  marker_result_id: number;
  file_name: string | null;
  validation_result: string | null;
  result: string | null;
  status: string | null;
  submitted_at: string;
};

export type SubmittedStudent = Student & {
  submission: Submission;
};

export type Course = {
  id: number;
  name: string | null;
  course_code: string | null;
  start_date: string | null;
  end_date: string | null;
  students: Student[];
  submitted_students: SubmittedStudent[];
};

export type CoursesResponse = {
  courses: Course[];
};