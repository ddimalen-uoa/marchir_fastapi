import React, { useEffect, useRef, useState } from "react";
import { useAuth } from "../features/auth/useAuth";
import { uploadFile, markAssginment, getLastSubmission } from "../api/api";

type ValidatorItem = {
  passed: boolean;
  message: string;
};

type ValidationApiResponse = {
  isOk: boolean;
  validators: Record<string, ValidatorItem[]>;
};

type LastSubmissionApiResponse = {
  file_name: string;
  submitted_at: string;
  status: string;
};

type SubmissionRecord = {
  fileName: string;
  submittedAt: string;
  status: string;
  validationResult: string;
};

type ValidationState =
  | { type: "idle" }
  | { type: "loading" }
  | { type: "submitting" }
  | { type: "error"; errors: string[] }
  | { type: "success" }
  | { type: "submitted"; submission: SubmissionRecord }
  | { type: "cancelled" };

function parseFailedValidatorMessages(data: ValidationApiResponse): string[] {
  const result: string[] = [];

  Object.entries(data.validators).forEach(([validatorName, items]) => {
    items.forEach((item) => {
      if (!item.passed) {
        result.push(`${validatorName}: ${item.message}`);
      }
    });
  });

  return result;
}

function mapSubmissionFromApi(data: LastSubmissionApiResponse): SubmissionRecord {
  return {
    fileName: data.file_name,
    submittedAt: new Date(data.submitted_at).toLocaleString(),
    status: data.status ?? "Submitted",
    validationResult: "Successful",
  };
}

export default function StudentDashboard() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { data } = useAuth();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationState, setValidationState] = useState<ValidationState>({ type: "idle" });
  const [lastSubmission, setLastSubmission] = useState<SubmissionRecord | null>(null);
  const [isFetchingLastSubmission, setIsFetchingLastSubmission] = useState(true);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setValidationState({ type: "idle" });
  };

  const handleClear = () => {
    setSelectedFile(null);
    setValidationState({ type: "idle" });

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleValidate = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    setValidationState({ type: "loading" });

    try {
      const response = await uploadFile(formData);
      const data: ValidationApiResponse = await response.json();

      if (!response.ok) {
        setValidationState({
          type: "error",
          errors: [
            "Something is wrong with your submission.",
            "Check that index.html is found in the ZIP file.",
            "Your ZIP file might be corrupted.",
            "Contact d.dimalen@auckland.ac.nz for assistance.",
          ],
        });
        return;
      }

      if (!data.isOk) {
        const messages = parseFailedValidatorMessages(data);

        setValidationState({
          type: "error",
          errors: messages.length > 0 ? messages : ["Validation failed."],
        });
        return;
      }

      setValidationState({ type: "success" });
    } catch (error) {
      console.error("Validation failed:", error);
      setValidationState({
        type: "error",
        errors: ["An unexpected error occurred while validating your submission."],
      });
    }
  };

  const handleCancel = () => {
    setValidationState({ type: "cancelled" });
  };

  const handleSubmit = async () => {
    if (!selectedFile || validationState.type !== "success") return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    setValidationState({ type: "submitting" });

    try {
      const response = await markAssginment(formData);

      if (!response.ok) {
        setValidationState({
          type: "error",
          errors: ["Failed to submit your assignment."],
        });
        return;
      }

      const now = new Date();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const year = now.getFullYear();

      const submission: SubmissionRecord = {
        fileName: `submission_${month}_${year}.zip`,
        submittedAt: now.toLocaleString(),
        status: "Submitted",
        validationResult: "Successful",
      };

      setLastSubmission(submission);
      setValidationState({ type: "submitted", submission });
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Submission failed:", error);
      setValidationState({
        type: "error",
        errors: ["An unexpected error occurred while submitting your assignment."],
      });
    }
  };

  const handleReupload = () => {
    handleClear();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const fetchLastSubmission = async () => {
      try {
        const response = await getLastSubmission();

        if (!response.ok) {
          console.error("Failed to fetch last submission:", response.status);
          return;
        }

        const data: LastSubmissionApiResponse | null = await response.json();

        if (!data) return;

        const submission = mapSubmissionFromApi(data);
        setLastSubmission(submission);
        // setValidationState({ type: "submitted", submission });
      } catch (error) {
        console.error("Failed to fetch last submission:", error);
      } finally {
        setIsFetchingLastSubmission(false);
      }
    };

    fetchLastSubmission();
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="bg-white border-b border-slate-200">
        <div className="flex items-center justify-between px-6 py-4 mx-auto max-w-7xl">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Student Dashboard</h1>
            <p className="text-sm text-slate-500">Upload and validate your ZIP submission</p>
          </div>

          <div className="px-4 py-2 text-sm font-medium text-blue-700 rounded-full bg-blue-50">
            Welcome, {data?.member.first_name ?? data?.member.upi ?? "Student"}.
          </div>
        </div>
      </header>

      <main className="px-6 py-10 mx-auto max-w-7xl">
        <div className="grid gap-8 lg:grid-cols-3">
          <section className="lg:col-span-2">
            <div className="p-6 bg-white border shadow-sm rounded-2xl border-slate-200">
              <div className="mb-6">
                <h2 className="text-xl font-semibold">New Submission</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Upload a ZIP file, validate its contents, and submit when ready.
                </p>
              </div>

              <div className="space-y-6">
                <div>
                  <label
                    htmlFor="zipFile"
                    className="block mb-2 text-sm font-medium text-slate-700"
                  >
                    ZIP File
                  </label>

                  <label
                    htmlFor="zipFile"
                    className="flex flex-col items-center justify-center px-6 py-10 text-center transition border-2 border-dashed cursor-pointer rounded-2xl border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50"
                  >
                    <svg
                      className="w-10 h-10 mb-3 text-slate-400"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 16V4m0 0-4 4m4-4 4 4M4 16.5A2.5 2.5 0 0 0 6.5 19h11a2.5 2.5 0 0 0 2.5-2.5M8 11l4 4 4-4"
                      />
                    </svg>

                    <span className="text-sm font-medium text-slate-700">
                      Click to choose a ZIP file
                    </span>
                    <span className="mt-1 text-xs text-slate-500">
                      Only .zip files are allowed
                    </span>

                    <input
                      ref={fileInputRef}
                      id="zipFile"
                      type="file"
                      accept=".zip,application/zip"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                  </label>

                  {selectedFile && (
                    <div className="px-4 py-3 mt-3 text-sm rounded-lg bg-slate-100 text-slate-700">
                      Selected file: {selectedFile.name}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={handleValidate}
                    disabled={!selectedFile || validationState.type === "loading"}
                    className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold text-white transition bg-blue-600 shadow-sm rounded-xl hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {validationState.type === "loading" ? "Validating..." : "Validate"}
                  </button>

                  <button
                    type="button"
                    onClick={handleClear}
                    className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold transition bg-white border rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <StatusPanel state={validationState} />

              {validationState.type === "success" && (
                <div className="flex flex-wrap gap-3 mt-6">
                  <button
                    type="button"
                    onClick={handleSubmit}
                    className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold text-white transition shadow-sm rounded-xl bg-emerald-600 hover:bg-emerald-700"
                  >
                    Ready to Submit
                  </button>

                  <button
                    type="button"
                    onClick={handleCancel}
                    className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold transition bg-white border rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </section>

          <aside className="lg:col-span-1">
            <div className="p-6 bg-white border shadow-sm rounded-2xl border-slate-200">
              <h2 className="text-lg font-semibold">Instructions</h2>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <p>1. Upload your ZIP file.</p>
                <p>
                  2. Click <span className="font-semibold text-slate-800">Validate</span> to parse
                  and check it.
                </p>
                <p>3. Review any errors if validation fails.</p>
                <p>
                  4. If validation succeeds, click{" "}
                  <span className="font-semibold text-slate-800">Ready to Submit</span>.
                </p>
                <p>5. After submission, your latest submission details will appear below.</p>
              </div>
            </div>
          </aside>
        </div>

        {!isFetchingLastSubmission && lastSubmission && (
          <section className="mt-8">
            <div className="p-6 bg-white border shadow-sm rounded-2xl border-slate-200">
              <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Last Submission</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Details of your most recently submitted ZIP file.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleReupload}
                  className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold text-white transition bg-blue-600 shadow-sm rounded-xl hover:bg-blue-700"
                >
                  Re-upload
                </button>
              </div>

              <div className="overflow-hidden border rounded-xl border-slate-200">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-3 text-xs font-semibold tracking-wide text-left uppercase text-slate-500">
                          File Name
                        </th>
                        <th className="px-4 py-3 text-xs font-semibold tracking-wide text-left uppercase text-slate-500">
                          Submitted At
                        </th>
                        <th className="px-4 py-3 text-xs font-semibold tracking-wide text-left uppercase text-slate-500">
                          Status
                        </th>
                        <th className="px-4 py-3 text-xs font-semibold tracking-wide text-left uppercase text-slate-500">
                          Validation Result
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                      <tr>
                        <td className="px-4 py-4 text-sm text-slate-700">
                          {lastSubmission.fileName}
                        </td>
                        <td className="px-4 py-4 text-sm text-slate-700">
                          {lastSubmission.submittedAt}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <span className="inline-flex px-3 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-700">
                            {lastSubmission.status}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-slate-700">
                          {lastSubmission.validationResult}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

type StatusPanelProps = {
  state: ValidationState;
};

function StatusPanel({ state }: StatusPanelProps) {
  if (state.type === "idle") return null;

  if (state.type === "loading") {
    return (
      <div className="p-5 mt-8 border border-blue-200 rounded-2xl bg-blue-50">
        <div className="flex items-start gap-3">
          <svg
            className="mt-0.5 h-5 w-5 animate-spin text-blue-600"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
            />
          </svg>

          <div>
            <p className="font-semibold text-blue-900">Validating upload...</p>
            <p className="mt-1 text-sm text-blue-700">
              Your ZIP file is being uploaded and parsed.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state.type === "error") {
    return (
      <div className="p-5 mt-8 border rounded-2xl border-rose-200 bg-rose-50">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-rose-500" />
          <div>
            <p className="font-semibold text-rose-900">Parsing failed</p>
            <p className="mt-1 text-sm text-rose-700">
              The upload was not successful. Review each error line below.
            </p>
          </div>
        </div>

        <ul className="mt-4 space-y-2">
          {state.errors.map((error, index) => (
            <li
              key={`${error}-${index}`}
              className="px-3 py-2 text-sm border rounded-lg border-rose-100 bg-white/70 text-rose-800"
            >
              {error}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (state.type === "success") {
    return (
      <div className="p-5 mt-8 border rounded-2xl border-emerald-200 bg-emerald-50">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <div>
            <p className="font-semibold text-emerald-900">Validation successful</p>
            <p className="mt-1 text-sm text-emerald-700">
              Your ZIP file passed validation and is ready to submit.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state.type === "submitted") {
    return (
      <div className="p-5 mt-8 border rounded-2xl border-emerald-200 bg-emerald-50">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <div>
            <p className="font-semibold text-emerald-900">Submission complete</p>
            <p className="mt-1 text-sm text-emerald-700">
              Your ZIP file has been successfully submitted.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state.type === "cancelled") {
    return (
      <div className="p-5 mt-8 border rounded-2xl border-slate-200 bg-slate-50">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-slate-400" />
          <div>
            <p className="font-semibold text-slate-800">Submission cancelled</p>
            <p className="mt-1 text-sm text-slate-600">
              You can choose another ZIP file and validate again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state.type === "submitting") {
    return (
      <div className="p-5 mt-8 border border-blue-200 rounded-2xl bg-blue-50">
        <div className="flex items-start gap-3">
          <svg
            className="mt-0.5 h-5 w-5 animate-spin text-blue-600"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
            />
          </svg>

          <div>
            <p className="font-semibold text-blue-900">Submitting...</p>
            <p className="mt-1 text-sm text-blue-700">
              Your ZIP file is being uploaded and recorded.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}