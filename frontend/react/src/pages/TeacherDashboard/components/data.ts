export type SubmissionStatus = "Submitted" | "Late" | "Pending Review";
export type ValidationResult = "Successful" | "Warnings" | "Failed";

export type Submission = {
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

export type Course = {
  id: string;
  code: string;
  title: string;
  term: string;
  totalStudents: number;
  submissions: Submission[];
};

export const courses: Course[] = [
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