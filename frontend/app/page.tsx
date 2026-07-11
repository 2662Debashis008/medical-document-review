"use client";

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Download,
  FileJson,
  FileText,
  Filter,
  Image as ImageIcon,
  Loader2,
  RefreshCcw,
  Search,
  Send,
  Settings,
  Stethoscope,
  Trash2,
  Upload,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteDocument,
  exportUrl,
  extractDocument,
  fileUrl,
  getApiStatus,
  getDocuments,
  getExtraction,
  getMetadata,
  getReview,
  saveReview,
  uploadDocument,
} from "@/services/api";
import { useUiStore } from "@/store/ui-store";
import type { DocumentCategory, MedicalDocument, ReviewStatus } from "@/types/api";

const uploadSchema = z.object({
  documentCategory: z.enum(["prescription", "xray"]),
  files: z
    .custom<FileList>()
    .refine((files) => files?.length > 0, "Select one or more medical documents."),
});

type UploadForm = z.infer<typeof uploadSchema>;
type ViewKey = "dashboard" | "upload" | "documents" | "review" | "export" | "settings";

const views: Array<{ key: ViewKey; label: string; icon: typeof Activity }> = [
  { key: "dashboard", label: "Dashboard", icon: Activity },
  { key: "upload", label: "Upload", icon: Upload },
  { key: "documents", label: "Documents", icon: FileText },
  { key: "review", label: "Review", icon: CheckCircle2 },
  { key: "export", label: "Export", icon: Download },
  { key: "settings", label: "Settings", icon: Settings },
];

export default function Home() {
  const queryClient = useQueryClient();
  const { activeView, setActiveView, selectedDocumentId, selectDocument, notice, setNotice } =
    useUiStore();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
    refetchInterval: (query) =>
      query.state.data?.some((document) => document.status === "processing") ? 3000 : false,
  });
  const statusQuery = useQuery({
    queryKey: ["api-status"],
    queryFn: getApiStatus,
    retry: 0,
  });

  const documents = documentsQuery.data ?? [];
  const selectedDocument =
    documents.find((document) => document.id === selectedDocumentId) ?? documents[0] ?? null;

  useEffect(() => {
    if (!selectedDocumentId && documents[0]) {
      selectDocument(documents[0].id);
    }
  }, [documents, selectDocument, selectedDocumentId]);

  const filteredDocuments = useMemo(() => {
    const term = search.trim().toLowerCase();
    return documents.filter((document) => {
      const status = displayStatus(document);
      const matchesTerm =
        !term ||
        document.original_filename.toLowerCase().includes(term) ||
        String(document.id).includes(term);
      const matchesStatus = statusFilter === "all" || status === statusFilter;
      const matchesCategory =
        categoryFilter === "all" || document.document_category === categoryFilter;
      return matchesTerm && matchesStatus && matchesCategory;
    });
  }, [categoryFilter, documents, search, statusFilter]);

  const stats = useMemo(() => {
    const total = documents.length;
    const approved = documents.filter((item) => displayStatus(item) === "approved").length;
    const rejected = documents.filter((item) => displayStatus(item) === "rejected").length;
    const processing = documents.filter((item) => item.status === "processing").length;
    const failed = documents.filter((item) => item.status === "failed").length;
    return { total, approved, rejected, processing, failed };
  }, [documents]);

  const invalidateDocuments = async () => {
    await queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-clinical text-white">
              <Stethoscope size={22} aria-hidden />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-ink">MedGemma Prescription Review</h1>
              <p className="text-sm text-slate-600">
                Structured prescription and X-ray extraction review
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill
              ok={statusQuery.isSuccess}
              label={
                statusQuery.isSuccess
                  ? `${statusQuery.data.status} API`
                  : statusQuery.isLoading
                    ? "Checking API"
                    : "API offline"
              }
            />
            <button
              className="icon-button"
              title="Refresh"
              onClick={() => {
                void invalidateDocuments();
                void statusQuery.refetch();
              }}
            >
              <RefreshCcw size={17} aria-hidden />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1760px] gap-5 px-4 py-5 sm:px-6">
        <aside className="rounded-md border border-slate-200 bg-white p-2 shadow-soft">
          <nav className="flex gap-1 overflow-x-auto">
            {views.map((view) => {
              const Icon = view.icon;
              const active = activeView === view.key;
              return (
                <button
                  key={view.key}
                  className={`flex h-10 shrink-0 items-center gap-2 rounded-md px-3 text-sm font-medium transition ${
                    active ? "bg-teal-50 text-clinical" : "text-slate-700 hover:bg-slate-100"
                  }`}
                  onClick={() => setActiveView(view.key)}
                >
                  <Icon size={17} aria-hidden />
                  {view.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <section className="min-w-0">
          {notice ? (
            <div className="mb-4 flex items-center justify-between rounded-md border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900">
              <span>{notice}</span>
              <button className="icon-button h-7 w-7" title="Dismiss" onClick={() => setNotice(null)}>
                <XCircle size={15} aria-hidden />
              </button>
            </div>
          ) : null}

          {activeView === "dashboard" ? <Dashboard stats={stats} documents={documents} /> : null}

          {activeView === "upload" ? (
            <UploadPanel
              onUploaded={async (documentIds) => {
                selectDocument(documentIds.at(-1) ?? null);
                setNotice(`${documentIds.length} document${documentIds.length === 1 ? "" : "s"} uploaded.`);
                await invalidateDocuments();
              }}
            />
          ) : null}

          {activeView === "documents" ? (
            <DocumentsPanel
              documents={filteredDocuments}
              allDocuments={documents}
              isLoading={documentsQuery.isLoading}
              selectedDocumentId={selectedDocumentId}
              search={search}
              statusFilter={statusFilter}
              categoryFilter={categoryFilter}
              onSearch={setSearch}
              onStatusFilter={setStatusFilter}
              onCategoryFilter={setCategoryFilter}
              onSelect={(documentId) => {
                selectDocument(documentId);
                setActiveView("review");
              }}
              onDeleted={async () => {
                setNotice("Document deleted.");
                await invalidateDocuments();
              }}
            />
          ) : null}

          {activeView === "review" ? (
            <ReviewPanel
              document={selectedDocument}
              documents={documents}
              onSelect={selectDocument}
              onChanged={async () => {
                setNotice("Workflow updated.");
                await invalidateDocuments();
              }}
            />
          ) : null}

          {activeView === "export" ? <ExportPanel document={selectedDocument} /> : null}

          {activeView === "settings" ? (
            <SettingsPanel apiStatus={statusQuery.data} apiOnline={statusQuery.isSuccess} />
          ) : null}
        </section>
      </div>
    </main>
  );
}

function Dashboard({
  stats,
  documents,
}: {
  stats: { total: number; approved: number; rejected: number; processing: number; failed: number };
  documents: MedicalDocument[];
}) {
  const recent = documents.slice(0, 6);
  const chartRows = [
    { label: "Uploaded", value: stats.total, color: "bg-slate-500" },
    { label: "Approved", value: stats.approved, color: "bg-emerald-600" },
    { label: "Rejected", value: stats.rejected, color: "bg-red-600" },
    { label: "Processing", value: stats.processing, color: "bg-amber-500" },
    { label: "Failed", value: stats.failed, color: "bg-rose-700" },
  ];
  const max = Math.max(1, ...chartRows.map((row) => row.value));

  return (
    <div className="grid gap-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Metric label="Total" value={stats.total} />
        <Metric label="Approved" value={stats.approved} tone="success" />
        <Metric label="Rejected" value={stats.rejected} tone="danger" />
        <Metric label="Processing" value={stats.processing} tone="warning" />
        <Metric label="Failed" value={stats.failed} tone="danger" />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <Panel title="Workflow Overview">
          <div className="grid gap-4">
            {chartRows.map((row) => (
              <div key={row.label} className="grid grid-cols-[96px_1fr_40px] items-center gap-3">
                <span className="text-sm text-slate-600">{row.label}</span>
                <div className="h-3 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className={`h-full ${row.color}`}
                    style={{ width: `${Math.max(4, (row.value / max) * 100)}%` }}
                  />
                </div>
                <span className="text-right text-sm font-semibold">{row.value}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Recent Documents">
          <div className="grid gap-2">
            {recent.length ? (
              recent.map((document) => <DocumentMini key={document.id} document={document} />)
            ) : (
              <EmptyState label="No documents uploaded yet." />
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function UploadPanel({ onUploaded }: { onUploaded: (documentIds: number[]) => Promise<void> }) {
  const { register, handleSubmit, reset, watch, formState } = useForm<UploadForm>({
    resolver: zodResolver(uploadSchema),
    defaultValues: { documentCategory: "prescription" },
  });
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);

  const mutation = useMutation({
    mutationFn: async (input: { files: FileList; category: DocumentCategory }) => {
      const ids: number[] = [];
      setProgress({ done: 0, total: input.files.length });
      for (const file of Array.from(input.files)) {
        const uploaded = await uploadDocument(file, input.category);
        ids.push(uploaded.document_id);
        setProgress({ done: ids.length, total: input.files.length });
      }
      return ids;
    },
    onSuccess: async (documentIds) => {
      reset({ documentCategory: "prescription", files: undefined as unknown as FileList });
      setProgress(null);
      await onUploaded(documentIds);
    },
    onError: () => setProgress(null),
  });

  const files = Array.from(watch("files") ?? []);

  return (
    <Panel title="Upload Medical Documents">
      <form
        className="grid gap-5"
        onSubmit={handleSubmit((values) => {
          mutation.mutate({
            files: values.files,
            category: values.documentCategory,
          });
        })}
      >
        <div className="grid gap-4 md:grid-cols-[240px_1fr]">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-700">Document category</span>
            <select className="control" {...register("documentCategory")}>
              <option value="prescription">Prescription</option>
              <option value="xray">X-ray</option>
              <option value="lab_report">Lab Report</option>
            </select>
          </label>
          <label className="grid min-h-40 cursor-pointer place-items-center rounded-md border-2 border-dashed border-slate-300 bg-panel px-4 py-6 text-center transition hover:border-clinical">
            <Upload size={28} className="mb-2 text-clinical" aria-hidden />
            <span className="text-sm font-semibold text-ink">
              {files.length ? `${files.length} selected` : "Choose JPG, JPEG, PNG, PDF, or TXT"}
            </span>
            <span className="mt-1 text-xs text-slate-600">
              Multiple PDFs are uploaded as separate documents and extracted independently
            </span>
            <input
              className="sr-only"
              type="file"
              accept=".jpg,.jpeg,.png,.pdf,.txt"
              multiple
              {...register("files")}
            />
          </label>
        </div>
        {files.length ? (
          <div className="grid gap-2 rounded-md border border-slate-200 bg-slate-50 p-3">
            {files.map((file) => (
              <div key={`${file.name}-${file.size}`} className="flex items-center gap-2 text-sm text-slate-700">
                <FileText size={15} className="text-clinical" aria-hidden />
                <span className="truncate">{file.name}</span>
              </div>
            ))}
          </div>
        ) : null}
        {progress ? (
          <ProgressLine label={`Uploading ${progress.done} of ${progress.total}`} value={progress.done / progress.total} />
        ) : null}
        {formState.errors.files ? (
          <p className="text-sm text-red-700">{formState.errors.files.message}</p>
        ) : null}
        {mutation.isError ? <ErrorBox message={readError(mutation.error)} /> : null}
        <div>
          <button className="primary-button" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="animate-spin" size={16} aria-hidden /> : <Upload size={16} aria-hidden />}
            Upload
          </button>
        </div>
      </form>
    </Panel>
  );
}

function DocumentsPanel(props: {
  documents: MedicalDocument[];
  allDocuments: MedicalDocument[];
  isLoading: boolean;
  selectedDocumentId: number | null;
  search: string;
  statusFilter: string;
  categoryFilter: string;
  onSearch: (value: string) => void;
  onStatusFilter: (value: string) => void;
  onCategoryFilter: (value: string) => void;
  onSelect: (documentId: number) => void;
  onDeleted: () => Promise<void>;
}) {
  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: props.onDeleted,
  });
  const statuses = Array.from(new Set(props.allDocuments.map(displayStatus)));

  return (
    <Panel title="Documents">
      <div className="mb-4 grid gap-3 lg:grid-cols-[1fr_180px_180px]">
        <label className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} aria-hidden />
          <input
            className="control w-full pl-9"
            value={props.search}
            onChange={(event) => props.onSearch(event.target.value)}
            placeholder="Search by filename or ID"
          />
        </label>
        <label className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} aria-hidden />
          <select
            className="control w-full pl-9"
            value={props.statusFilter}
            onChange={(event) => props.onStatusFilter(event.target.value)}
          >
            <option value="all">All statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {statusLabel(status)}
              </option>
            ))}
          </select>
        </label>
        <select
          className="control"
          value={props.categoryFilter}
          onChange={(event) => props.onCategoryFilter(event.target.value)}
        >
          <option value="all">All categories</option>
          <option value="prescription">Prescription</option>
          <option value="xray">X-ray</option>
          <option value="lab_report">Lab Report</option>
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <th className="py-3 pr-3">ID</th>
              <th className="py-3 pr-3">File</th>
              <th className="py-3 pr-3">Category</th>
              <th className="py-3 pr-3">Type</th>
              <th className="py-3 pr-3">Status</th>
              <th className="py-3 pr-3">Created</th>
              <th className="py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {props.documents.map((document) => (
              <tr
                key={document.id}
                className={`border-b border-slate-100 ${props.selectedDocumentId === document.id ? "bg-teal-50/50" : ""}`}
              >
                <td className="py-3 pr-3 font-semibold">{document.id}</td>
                <td className="max-w-[280px] truncate py-3 pr-3">{document.original_filename}</td>
                <td className="py-3 pr-3 capitalize">{document.document_category}</td>
                <td className="py-3 pr-3 capitalize">{document.file_type}</td>
                <td className="py-3 pr-3">
                  <Badge status={displayStatus(document)} />
                </td>
                <td className="py-3 pr-3">{formatDate(document.created_at)}</td>
                <td className="py-3">
                  <div className="flex justify-end gap-2">
                    <button className="secondary-button h-9" onClick={() => props.onSelect(document.id)}>
                      Review
                    </button>
                    <button
                      className="icon-button"
                      title="Delete"
                      disabled={deleteMutation.isPending}
                      onClick={() => deleteMutation.mutate(document.id)}
                    >
                      <Trash2 size={16} aria-hidden />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!props.documents.length && props.isLoading ? <LoadingState label="Loading documents" /> : null}
        {!props.documents.length && !props.isLoading ? <EmptyState label="No matching documents." /> : null}
      </div>
    </Panel>
  );
}

function ReviewPanel({
  document,
  documents,
  onSelect,
  onChanged,
}: {
  document: MedicalDocument | null;
  documents: MedicalDocument[];
  onSelect: (documentId: number | null) => void;
  onChanged: () => Promise<void>;
}) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [editedJson, setEditedJson] = useState("");
  const [jsonError, setJsonError] = useState<string | null>(null);

  const extractionQuery = useQuery({
    queryKey: ["extraction", document?.id],
    queryFn: () => getExtraction(document!.id),
    enabled: Boolean(document?.id),
    retry: 0,
  });
  const reviewQuery = useQuery({
    queryKey: ["review", document?.id],
    queryFn: () => getReview(document!.id),
    enabled: Boolean(document?.id),
    retry: 0,
  });
  const metadataQuery = useQuery({
    queryKey: ["metadata", document?.id],
    queryFn: () => getMetadata(document!.id),
    enabled: Boolean(document?.id),
    retry: 0,
  });

  const extractedData = reviewQuery.data?.reviewed_data ?? extractionQuery.data?.extracted_data ?? null;
  const editedData = useMemo(() => {
    if (!editedJson.trim()) {
      return extractedData;
    }
    try {
      return JSON.parse(editedJson) as Record<string, unknown>;
    } catch {
      return extractedData;
    }
  }, [editedJson, extractedData]);
  const extractionError =
    readOptionalApiError(extractionQuery.error) ??
    readOptionalApiError(metadataQuery.error) ??
    metadataQuery.data?.errors ??
    document?.extraction_error ??
    null;
  const hasExtraction = Boolean(extractedData);

  const extractMutation = useMutation({
    mutationFn: extractDocument,
    onMutate: async () => {
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["extraction", document?.id] });
      await queryClient.invalidateQueries({ queryKey: ["metadata", document?.id] });
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      await onChanged();
    },
    onError: async () => {
      await queryClient.invalidateQueries({ queryKey: ["metadata", document?.id] });
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const reviewMutation = useMutation({
    mutationFn: (status: ReviewStatus) =>
      saveReview({
        documentId: document!.id,
        status,
        reviewer_notes: notes,
        reviewed_data: parseEditedExtraction(editedJson) ?? extractedData ?? {},
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["review", document?.id] });
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      await onChanged();
    },
  });

  useEffect(() => {
    setNotes(reviewQuery.data?.reviewer_notes ?? "");
  }, [document?.id, reviewQuery.data?.reviewer_notes]);

  useEffect(() => {
    setEditedJson(extractedData ? JSON.stringify(extractedData, null, 2) : "");
    setJsonError(null);
  }, [document?.id, extractedData]);

  if (!document) {
    return (
      <Panel title="Review">
        <EmptyState label="Select or upload a document to begin review." />
      </Panel>
    );
  }

  const extracting = extractMutation.isPending || document.status === "processing";

  return (
    <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
      <DocumentSidebar documents={documents} selectedId={document.id} onSelect={onSelect} />

      <div className="grid gap-5">
        <Panel title={`Review Document #${document.id}`}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge status={displayStatus(document)} />
                <span className="text-xs uppercase text-slate-500">{document.document_category}</span>
                <span className="text-xs uppercase text-slate-500">{document.file_type}</span>
              </div>
              <p className="truncate text-sm font-medium text-ink">{document.original_filename}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a className="secondary-button" href={fileUrl(document.id)} download>
                <Download size={16} aria-hidden />
                Download
              </a>
              <button
                className="primary-button"
                disabled={extracting}
                onClick={() => extractMutation.mutate(document.id)}
              >
                {extracting ? <Loader2 className="animate-spin" size={16} aria-hidden /> : <Send size={16} aria-hidden />}
                {hasExtraction ? "Retry Extraction" : "Extract"}
              </button>
            </div>
          </div>

          {extracting ? <ProgressLine label="Extraction in progress" value={0.62} indeterminate /> : null}
          {extractMutation.isError ? (
            <ErrorBox
              message={readError(extractMutation.error)}
              actionLabel="Retry"
              onAction={() => extractMutation.mutate(document.id)}
            />
          ) : null}
          {!extractMutation.isError && extractionError && !hasExtraction ? (
            <ErrorBox
              message={extractionError}
              actionLabel="Retry"
              onAction={() => extractMutation.mutate(document.id)}
            />
          ) : null}

          <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(420px,0.95fr)_minmax(520px,1.05fr)]">
            <div>
              <SectionTitle title="Preview" />
              <FilePreview document={document} />
            </div>
            <div className="grid content-start gap-4">
              <SectionTitle title="Extraction Results" />
              {extractionQuery.isFetching && !hasExtraction ? <LoadingState label="Loading extraction" /> : null}
              {hasExtraction ? (
                <>
                  <StructuredExtraction data={editedData} category={document.document_category} />
                  <JsonReviewEditor
                    value={editedJson}
                    error={jsonError}
                    onChange={(value) => {
                      setEditedJson(value);
                      setJsonError(null);
                    }}
                    onFormat={() => {
                      const parsed = parseEditedExtraction(editedJson);
                      if (!parsed) {
                        setJsonError("JSON is invalid. Fix it before saving the review.");
                        return;
                      }
                      setEditedJson(JSON.stringify(parsed, null, 2));
                      setJsonError(null);
                    }}
                  />
                </>
              ) : !extractionQuery.isFetching ? (
                <EmptyState label="Run extraction to see structured patient, medicine, diagnosis, and finding sections." />
              ) : null}

              <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <label className="grid gap-2">
                  <span className="text-sm font-semibold text-ink">Reviewer notes</span>
                  <textarea
                    className="control min-h-24 w-full py-3"
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    placeholder="Add notes for audit or follow-up"
                  />
                </label>
                {reviewMutation.isError ? (
                  <p className="mt-2 text-sm text-red-700">{readError(reviewMutation.error)}</p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    className="primary-button bg-emerald-700 hover:bg-emerald-800"
                    disabled={reviewMutation.isPending || !hasExtraction || Boolean(jsonError)}
                    onClick={() => {
                      if (!parseEditedExtraction(editedJson)) {
                        setJsonError("JSON is invalid. Fix it before saving the review.");
                        return;
                      }
                      reviewMutation.mutate("approved");
                    }}
                  >
                    <CheckCircle2 size={16} aria-hidden />
                    Approve
                  </button>
                  <button
                    className="secondary-button"
                    disabled={reviewMutation.isPending || !hasExtraction || Boolean(jsonError)}
                    onClick={() => {
                      if (!parseEditedExtraction(editedJson)) {
                        setJsonError("JSON is invalid. Fix it before saving the review.");
                        return;
                      }
                      reviewMutation.mutate("needs_changes");
                    }}
                  >
                    Needs Changes
                  </button>
                  <button
                    className="danger-button"
                    disabled={reviewMutation.isPending || !hasExtraction || Boolean(jsonError)}
                    onClick={() => {
                      if (!parseEditedExtraction(editedJson)) {
                        setJsonError("JSON is invalid. Fix it before saving the review.");
                        return;
                      }
                      reviewMutation.mutate("rejected");
                    }}
                  >
                    <XCircle size={16} aria-hidden />
                    Reject
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Metadata">
          {metadataQuery.data ? (
            <dl className="grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
              <Meta label="Model" value={metadataQuery.data.model_name} />
              <Meta label="Runtime" value={metadataQuery.data.runtime} />
              <Meta label="Prompt" value={metadataQuery.data.prompt_version} />
              <Meta label="Latency" value={formatSeconds(metadataQuery.data.latency)} />
              <Meta label="Processing" value={formatSeconds(metadataQuery.data.processing_time)} />
              <Meta label="Errors" value={metadataQuery.data.errors ?? "None"} />
            </dl>
          ) : (
            <EmptyState label="Metadata appears after extraction." />
          )}
        </Panel>
      </div>
    </div>
  );
}

function DocumentSidebar({
  documents,
  selectedId,
  onSelect,
}: {
  documents: MedicalDocument[];
  selectedId: number;
  onSelect: (documentId: number | null) => void;
}) {
  return (
    <aside className="rounded-md border border-slate-200 bg-white p-3 shadow-soft lg:sticky lg:top-5 lg:h-fit">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Uploaded Documents</h2>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
          {documents.length}
        </span>
      </div>
      <div className="grid max-h-[720px] gap-2 overflow-y-auto pr-1">
        {documents.map((item) => {
          const Icon = item.file_type === "image" ? ImageIcon : FileText;
          const selected = selectedId === item.id;
          return (
            <button
              key={item.id}
              className={`grid gap-2 rounded-md border p-3 text-left transition ${
                selected ? "border-clinical bg-teal-50" : "border-slate-200 hover:bg-slate-50"
              }`}
              onClick={() => onSelect(item.id)}
            >
              <div className="flex min-w-0 items-center gap-2">
                <Icon size={16} className="shrink-0 text-clinical" aria-hidden />
                <span className="truncate text-sm font-medium text-ink">{item.original_filename}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs capitalize text-slate-500">{item.document_category}</span>
                <Badge status={displayStatus(item)} compact />
              </div>
            </button>
          );
        })}
        {!documents.length ? <EmptyState label="No documents." /> : null}
      </div>
    </aside>
  );
}

function ExportPanel({ document }: { document: MedicalDocument | null }) {
  return (
    <Panel title="Export Current Document">
      {document ? (
        <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge status={displayStatus(document)} />
              <span className="text-xs uppercase text-slate-500">Document #{document.id}</span>
            </div>
            <p className="truncate text-sm font-semibold text-ink">{document.original_filename}</p>
            <p className="mt-1 text-sm text-slate-500">
              Export includes extraction data, review status, reviewer notes, and run metadata for this document only.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a className="secondary-button" href={exportUrl("json", document.id)} download>
              <FileJson size={16} aria-hidden />
              Download JSON
            </a>
            <a className="primary-button" href={exportUrl("csv", document.id)}>
              <Download size={16} aria-hidden />
              CSV
            </a>
          </div>
        </div>
      ) : (
        <EmptyState label="Select a document before exporting." />
      )}
    </Panel>
  );
}

function SettingsPanel({
  apiStatus,
  apiOnline,
}: {
  apiStatus?: { app: string; version: string; status: string };
  apiOnline: boolean;
}) {
  return (
    <div className="grid gap-5">
      <Panel title="API Status">
        <dl className="grid gap-3 text-sm sm:grid-cols-3">
          <Meta label="Connection" value={apiOnline ? "Online" : "Offline"} />
          <Meta label="Application" value={apiStatus?.app ?? "Unavailable"} />
          <Meta label="Version" value={apiStatus?.version ?? "Unavailable"} />
        </dl>
      </Panel>
      <Panel title="Prompt Information">
        <div className="grid gap-3 text-sm text-slate-700 md:grid-cols-3">
          <PromptInfo title="Prescription" file="prescription_prompt.txt" />
          <PromptInfo title="X-ray Image" file="xray_image_prompt.txt" />
          <PromptInfo title="X-ray Report" file="xray_report_prompt.txt" />
        </div>
      </Panel>
    </div>
  );
}

function StructuredExtraction({
  data,
  category,
}: {
  data: Record<string, unknown> | null;
  category: DocumentCategory;
}) {
  if (!data) {
    return <EmptyState label="No extraction data available." />;
  }
  if (category === "lab_report") {
    return <LabReportResult data={data} />;
  }
  if (category === "prescription") {
    const prescriptions =
      data.schema_version === "v2.0"
        ? [data]
        : asArray<Record<string, unknown>>(data.prescriptions);
    return (
      <div className="grid gap-4">
        {prescriptions.map((prescription, index) => (
          <PrescriptionResult
            key={index}
            prescription={prescription}
            title={prescriptions.length > 1 ? `Prescription ${index + 1}` : "Prescription"}
          />
        ))}
        {!prescriptions.length ? <GenericStructuredData data={data} /> : null}
      </div>
    );
  }

  const xrays = asArray<Record<string, unknown>>(data.xrays);
  if (xrays.length) {
    return (
      <div className="grid gap-4">
        {xrays.map((xray, index) => (
          <XrayResult key={index} xray={xray} title={xrays.length > 1 ? `X-ray ${index + 1}` : "X-ray"} />
        ))}
      </div>
    );
  }

  return <XrayResult xray={data} title="X-ray" />;
}

function LabReportResult({ data }: { data: Record<string, unknown> }) {
  const laboratory = asRecord(data.laboratory);
  const patient = asRecord(data.patient);
  const panels = asArray<Record<string, unknown>>(data.panels);

  return (
    <div className="grid gap-4">
      <SectionCard title="Patient & Laboratory Details">
        <KeyGrid
          items={[
            ["Patient", valueText(patient.name)],
            ["Age", valueText(patient.age)],
            ["Sex", valueText(patient.sex)],
            ["Lab Name", valueText(laboratory.name)],
            ["Referred By", valueText(laboratory.referred_by)],
            ["Report Date", valueText(data.report_date ?? laboratory.datetime_on_doc)],
          ]}
        />
      </SectionCard>
      
      {panels.map((panel, idx) => {
        const tests = asArray<Record<string, unknown>>(panel.tests);
        return (
          <SectionCard key={idx} title={valueText(panel.panel_name || "General Pathology")}>
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full min-w-[500px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Test Name</th>
                    <th className="px-3 py-2">Result</th>
                    <th className="px-3 py-2">Unit</th>
                    <th className="px-3 py-2">Reference Range</th>
                    <th className="px-3 py-2">Flag</th>
                  </tr>
                </thead>
                <tbody>
                  {tests.map((test, tIdx) => {
                    const flag = valueText(test.flag).trim().toLowerCase();
                    const isAbnormal = flag === "high" || flag === "low";
                    const flagColor = flag === "high" ? "text-red-600 font-bold" : flag === "low" ? "text-amber-600 font-bold" : "text-slate-600";
                    const valColor = isAbnormal ? (flag === "high" ? "text-red-700 font-semibold" : "text-amber-700 font-semibold") : "text-ink";

                    return (
                      <tr key={tIdx} className="border-t border-slate-100">
                        <td className="px-3 py-2 font-medium text-ink">
                          {valueText(test.test_name)}
                        </td>
                        <td className={`px-3 py-2 ${valColor}`}>
                          {valueText(test.result)}
                        </td>
                        <td className="px-3 py-2 text-slate-600">
                          {valueText(test.unit)}
                        </td>
                        <td className="px-3 py-2 text-slate-600">
                          {valueText(test.reference_range)}
                        </td>
                        <td className={`px-3 py-2 ${flagColor}`}>
                          {flag ? flag.toUpperCase() : "NORMAL"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </SectionCard>
        );
      })}
      
      {!panels.length ? <EmptyState label="No test panels found." /> : null}
    </div>
  );
}

function PrescriptionResult({
  prescription,
  title,
}: {
  prescription: Record<string, unknown>;
  title: string;
}) {
  const isV2 = prescription.schema_version === "v2.0";
  const patient = asRecord(prescription.patient);
  const facility = asRecord(prescription.document_facility);
  const consultant = asRecord(facility.consultant);
  const advice = asRecord(prescription.advice_plan_facts);
  const inferences = asRecord(prescription.interpretation_inferences);
  const medicines = isV2
    ? asArray<Record<string, unknown>>(prescription.medications_facts)
    : asArray<Record<string, unknown>>(prescription.medications);

  return (
    <SectionCard title={title}>
      <div className="grid gap-4">
        <KeyGrid
          items={[
            ["Patient", valueText(isV2 ? patient.name : prescription.patient_name)],
            ["Age", valueText(isV2 ? patient.age : prescription.age)],
            ["Sex", valueText(isV2 ? patient.sex : prescription.gender)],
            ["Doctor", valueText(isV2 ? consultant.name : prescription.doctor_name)],
            ["Facility", valueText(facility.facility)],
            ["Date", valueText(isV2 ? facility.datetime_on_doc : prescription.date)],
          ]}
        />
        <MedicineTable medicines={medicines} />
        <ListSection title="Complaints / History" values={toTextList(prescription.history_presenting_complaints_facts)} compact />
        <ListSection title="Diagnoses" values={toTextList(inferences.working_diagnoses)} compact />
        <ListSection title="Investigations" values={toTextList(prescription.investigations_facts)} compact />
        <KeyGrid
          items={[
            ["Diet / Lifestyle", valueText(advice.diet_lifestyle)],
            ["Follow-up", valueText(advice.follow_up)],
            ["Referral / Admission", valueText(advice.referrals_or_admission)],
            ["Instructions", valueText(advice.special_instructions)],
          ]}
        />
        <ListSection
          title="Uncertain or Illegible"
          values={toTextList(prescription.uncertain_or_illegible_segments ?? prescription.uncertainty_notes)}
          compact
        />
      </div>
    </SectionCard>
  );
}

function XrayResult({ xray, title }: { xray: Record<string, unknown>; title: string }) {
  return (
    <SectionCard title={title}>
      <div className="grid gap-4">
        {xray.schema_version === "xray_v2.0" ? (
          <KeyGrid
            items={[
              ["Patient", valueText(asRecord(xray.patient).name)],
              ["Age", valueText(asRecord(xray.patient).age)],
              ["Sex", valueText(asRecord(xray.patient).sex)],
              ["Body part", valueText(asRecord(xray.xray_study).body_part)],
              ["Study type", valueText(asRecord(xray.xray_study).study_type)],
              ["View", valueText(asRecord(xray.xray_study).view)],
            ]}
          />
        ) : (
          <KeyGrid
            items={[
              ["Body part", valueText(xray.body_part)],
              ["Study type", valueText(xray.study_type)],
              ["Confidence", valueText(xray.confidence)],
            ]}
          />
        )}
        {xray.schema_version === "xray_v2.0" ? <TextField label="Visual Understanding" value={valueText(xray.visual_understanding)} /> : null}
        <ListSection title="Findings" values={toTextList(xray.findings_facts ?? xray.findings)} compact />
        <ListSection title="Observations" values={toTextList(xray.observations)} compact />
        <ListSection title="Impression" values={toTextList(xray.impression)} compact />
        <ListSection title="Possible Abnormalities" values={toTextList(asRecord(xray.interpretation_inferences).possible_abnormalities ?? xray.possible_abnormalities)} compact />
        <ListSection
          title="Recommendations"
          values={toTextList(asRecord(xray.advice_plan_facts).recommendations ?? xray.recommendation)}
          compact
        />
        <ListSection title="Uncertainty Notes" values={toTextList(xray.uncertain_or_illegible_segments ?? xray.uncertainty_notes)} compact />
      </div>
    </SectionCard>
  );
}

function JsonReviewEditor({
  value,
  error,
  onChange,
  onFormat,
}: {
  value: string;
  error: string | null;
  onChange: (value: string) => void;
  onFormat: () => void;
}) {
  return (
    <SectionCard title="Editable JSON">
      <div className="grid gap-3">
        <textarea
          className="control min-h-72 w-full font-mono text-xs leading-5"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          spellCheck={false}
        />
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <div>
          <button className="secondary-button" type="button" onClick={onFormat}>
            <FileJson size={16} aria-hidden />
            Validate & Format
          </button>
        </div>
      </div>
    </SectionCard>
  );
}

function MedicineTable({ medicines }: { medicines: Array<Record<string, unknown>> }) {
  if (!medicines.length) {
    return <EmptyState label="No medicines found." />;
  }
  return (
    <div className="overflow-x-auto rounded-md border border-slate-200">
      <table className="w-full min-w-[620px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
          <tr>
            <th className="px-3 py-2">Medicine</th>
            <th className="px-3 py-2">Dosage</th>
            <th className="px-3 py-2">Frequency</th>
            <th className="px-3 py-2">Route</th>
            <th className="px-3 py-2">Duration</th>
            <th className="px-3 py-2">Instructions</th>
          </tr>
        </thead>
        <tbody>
          {medicines.map((medicine, index) => (
            <tr key={index} className="border-t border-slate-100">
              <td className="px-3 py-2 font-medium text-ink">
                {valueText(medicine.medication_name ?? asRecord(medicine.drug).name)}
              </td>
              <td className="px-3 py-2">
                {(() => {
                  const dosageStr = medicine.dosage ?? asRecord(medicine.dose).amount;
                  const strengthStr = asRecord(medicine.drug).strength;
                  const unitStr = medicine.unit ?? asRecord(medicine.dose).unit;
                  
                  const parts = [];
                  if (strengthStr) {
                    parts.push(strengthStr);
                  }
                  if (dosageStr && dosageStr !== strengthStr) {
                    if (strengthStr) {
                      parts.push(`(${dosageStr}${unitStr ? ' ' + unitStr : ''})`);
                    } else {
                      parts.push(dosageStr);
                      if (unitStr) parts.push(unitStr);
                    }
                  } else if (unitStr) {
                    parts.push(unitStr);
                  }
                  
                  return parts.filter(Boolean).join(" ") || "Unavailable";
                })()}
              </td>
              <td className="px-3 py-2">{humanizeFrequency(medicine.frequency ?? medicine.timing ?? medicine.verbatim_line)}</td>
              <td className="px-3 py-2">{humanizeRoute(medicine.route)}</td>
              <td className="px-3 py-2">{valueText(medicine.duration)}</td>
              <td className="px-3 py-2">
                {humanizeInstruction(medicine.instructions ?? medicine.timing ?? medicine.verbatim_line)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GenericStructuredData({ data }: { data: Record<string, unknown> }) {
  return (
    <SectionCard title="Extracted Fields">
      <div className="grid gap-2">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="grid gap-1 rounded-md bg-slate-50 p-2">
            <span className="text-xs uppercase text-slate-500">{key.replaceAll("_", " ")}</span>
            <span className="break-words text-sm font-medium text-ink">{valueText(value)}</span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function FilePreview({ document }: { document: MedicalDocument }) {
  const url = fileUrl(document.id);
  if (document.file_type === "image") {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        className="h-[620px] w-full rounded-md border border-slate-200 bg-slate-50 object-contain"
        src={url}
        alt={document.original_filename}
      />
    );
  }
  return (
    <iframe
      className="h-[620px] w-full rounded-md border border-slate-200 bg-white"
      src={url}
      title={document.original_filename}
    />
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 shadow-soft">
      <h2 className="mb-4 text-base font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
      <SectionTitle title={title} />
      {children}
    </div>
  );
}

function SectionTitle({ title }: { title: string }) {
  return <h3 className="mb-2 text-sm font-semibold text-ink">{title}</h3>;
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "danger" | "success" | "warning";
}) {
  const color =
    tone === "danger" ? "text-red-700" : tone === "success" ? "text-emerald-700" : tone === "warning" ? "text-amber-700" : "text-ink";
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-soft">
      <p className="text-sm text-slate-600">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex h-9 items-center gap-2 rounded-md border px-3 text-sm font-medium ${
        ok ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-red-200 bg-red-50 text-red-800"
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-600" : "bg-red-600"}`} />
      {label}
    </span>
  );
}

function Badge({ status, compact = false }: { status: string; compact?: boolean }) {
  const tone =
    status === "failed" || status === "rejected"
      ? "border-red-200 bg-red-50 text-red-800"
      : status === "approved"
        ? "border-emerald-200 bg-emerald-50 text-emerald-800"
        : status === "processing"
          ? "border-amber-200 bg-amber-50 text-amber-800"
          : status === "processed"
            ? "border-teal-200 bg-teal-50 text-teal-800"
            : "border-slate-200 bg-slate-50 text-slate-700";
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${tone}`}>
      {compact ? statusLabel(status).replace("✅ ", "").replace("❌ ", "") : statusLabel(status)}
    </span>
  );
}

function DocumentMini({ document }: { document: MedicalDocument }) {
  const Icon = document.file_type === "image" ? ImageIcon : FileText;
  return (
    <div className="flex items-center gap-3 rounded-md border border-slate-200 p-3">
      <Icon size={18} className="text-clinical" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink">{document.original_filename}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <span className="text-xs capitalize text-slate-500">{document.document_category}</span>
          <Badge status={displayStatus(document)} compact />
        </div>
      </div>
    </div>
  );
}

function KeyGrid({ items }: { items: Array<[string, string]> }) {
  return (
    <dl className="grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-3">
      {items.map(([label, value]) => (
        <Meta key={label} label={label} value={value} />
      ))}
    </dl>
  );
}

function ListSection({ title, values, compact = false }: { title: string; values: string[]; compact?: boolean }) {
  if (!values.length) {
    return null;
  }
  const content = (
    <ul className="grid gap-2 text-sm text-slate-700">
      {values.map((value, index) => (
        <li key={`${value}-${index}`} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
          {value}
        </li>
      ))}
    </ul>
  );
  if (compact) {
    return (
      <div>
        <SectionTitle title={title} />
        {content}
      </div>
    );
  }
  return (
    <SectionCard title={title}>
      {content}
    </SectionCard>
  );
}

function Meta({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <dt className="text-[11px] uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 min-h-5 break-words font-medium text-ink">{value ?? "Unavailable"}</dd>
    </div>
  );
}

function TextField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 whitespace-pre-line text-sm font-medium text-ink">{value}</p>
    </div>
  );
}

function PromptInfo({ title, file }: { title: string; file: string }) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-1 font-mono text-xs text-slate-500">{file}</p>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-panel px-4 py-8 text-center text-sm text-slate-600">
      {label}
    </div>
  );
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
      <Loader2 className="animate-spin" size={15} aria-hidden />
      {label}
    </div>
  );
}

function ErrorBox({
  message,
  actionLabel,
  onAction,
}: {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="my-3 flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-800">
      <span className="inline-flex items-center gap-2">
        <AlertCircle size={16} aria-hidden />
        {message}
      </span>
      {actionLabel && onAction ? (
        <button className="secondary-button h-8 border-red-200 bg-white text-red-800 hover:bg-red-100" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

function ProgressLine({
  label,
  value,
  indeterminate = false,
}: {
  label: string;
  value: number;
  indeterminate?: boolean;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <div className="flex items-center gap-2">
        <Loader2 className="animate-spin" size={15} aria-hidden />
        {label}
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-amber-100">
        <div
          className={`h-full bg-amber-500 ${indeterminate ? "animate-pulse" : ""}`}
          style={{ width: `${Math.max(8, Math.min(100, value * 100))}%` }}
        />
      </div>
    </div>
  );
}

function displayStatus(document: MedicalDocument) {
  return document.review_status ?? document.status ?? "uploaded";
}

function statusLabel(status: string) {
  if (status === "approved") {
    return "Approved";
  }
  if (status === "rejected") {
    return "Rejected";
  }
  if (status === "needs_changes") {
    return "Needs Changes";
  }
  if (status === "uploaded") {
    return "Pending";
  }
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatSeconds(value?: number | null) {
  if (value === null || value === undefined) {
    return "Unavailable";
  }
  return `${value.toFixed(2)}s`;
}

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }
  if (Array.isArray(value)) {
    return value.map(valueText).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function parseEditedExtraction(value: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) {
    return value.map(valueText).filter((item) => item !== "Unavailable");
  }
  const text = valueText(value);
  return text === "Unavailable" ? [] : [text];
}

const frequencyMap: Record<string, string> = {
  od: "Once Daily",
  bd: "Twice Daily",
  tds: "Three Times Daily",
  tid: "Three Times Daily",
  qid: "Four Times Daily",
  hs: "At Bedtime",
  ac: "Before Meals",
  pc: "After Meals",
  prn: "As Needed",
  sos: "Only When Required",
  stat: "Immediately",
};

const timingPatternMap: Record<string, string> = {
  "1-0-0": "Once Daily (Morning)",
  "0-1-0": "Once Daily (Afternoon/Lunch)",
  "0-0-1": "Once Daily (Night)",
  "1-0-1": "Twice Daily (Morning and Night)",
  "1-1-0": "Twice Daily (Morning and Afternoon)",
  "0-1-1": "Twice Daily (Afternoon and Night)",
  "1-1-1": "Three Times Daily (Morning, Afternoon and Night)",
  "1-1-1-1": "Four Times Daily",
};

const routeMap: Record<string, string> = {
  po: "Oral",
  iv: "Intravenous",
  im: "Intramuscular",
  sc: "Subcutaneous",
  topical: "Apply on Skin",
};

function humanizeFrequency(value: unknown) {
  const text = valueText(value);
  if (text === "Unavailable") {
    return text;
  }
  const normalized = text.trim().toLowerCase();
  const compact = normalized.replace(/\s+/g, "");
  const pattern = text.match(/\b[01](?:-[01]){2,3}\b/)?.[0];
  if (pattern && timingPatternMap[pattern]) {
    return timingPatternMap[pattern];
  }
  if (frequencyMap[compact]) {
    return frequencyMap[compact];
  }
  const abbreviation = Object.keys(frequencyMap).find((key) =>
    new RegExp(`\\b${key}\\b`, "i").test(text),
  );
  return abbreviation ? frequencyMap[abbreviation] : text;
}

function humanizeRoute(value: unknown) {
  const text = valueText(value);
  if (text === "Unavailable") {
    return text;
  }
  return routeMap[text.trim().toLowerCase()] ?? text;
}

function humanizeInstruction(value: unknown) {
  const text = valueText(value);
  if (text === "Unavailable") {
    return text;
  }
  const pieces = new Set<string>();
  const pattern = text.match(/\b[01](?:-[01]){2,3}\b/)?.[0];
  if (pattern && timingPatternMap[pattern]) {
    pieces.add(timingPatternMap[pattern]);
  }
  for (const key of Object.keys(frequencyMap)) {
    if (new RegExp(`\\b${key}\\b`, "i").test(text)) {
      pieces.add(frequencyMap[key]);
    }
  }
  for (const key of Object.keys(routeMap)) {
    if (new RegExp(`\\b${key}\\b`, "i").test(text)) {
      pieces.add(routeMap[key]);
    }
  }
  return pieces.size ? `${text} (${Array.from(pieces).join("; ")})` : text;
}

function readOptionalApiError(error: unknown) {
  const message = readError(error);
  if (!message || message === "Extraction not found" || message === "Metadata not found" || message === "Request failed.") {
    return null;
  }
  return message;
}

function readError(error: unknown) {
  if (!error) {
    return "Request failed.";
  }
  if (typeof error === "object" && "response" in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed.";
}
