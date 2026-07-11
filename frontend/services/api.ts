import axios from "axios";
import type {
  DocumentCategory,
  ExtractResponse,
  ExtractionResponse,
  MedicalDocument,
  MetadataResponse,
  ReviewResponse,
  ReviewStatus,
  UploadResponse,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export async function getApiStatus() {
  const { data } = await api.get("/");
  return data as { app: string; version: string; status: string };
}

export async function getDocuments() {
  const { data } = await api.get<MedicalDocument[]>("/documents");
  return data;
}

export async function uploadDocument(file: File, documentCategory: DocumentCategory) {
  const form = new FormData();
  form.append("file", file);
  form.append("document_category", documentCategory);
  const { data } = await api.post<UploadResponse>("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteDocument(documentId: number) {
  const { data } = await api.delete<{ message: string }>(`/documents/${documentId}`);
  return data;
}

export async function extractDocument(documentId: number) {
  const { data } = await api.post<ExtractResponse>("/extract", {
    document_id: documentId,
  });
  return data;
}

export async function getExtraction(documentId: number) {
  const { data } = await api.get<ExtractionResponse>(`/documents/${documentId}/extraction`);
  return data;
}

export async function getReview(documentId: number) {
  const { data } = await api.get<ReviewResponse>(`/review/${documentId}`);
  return data;
}

export async function saveReview(input: {
  documentId: number;
  status: ReviewStatus;
  reviewer_notes?: string;
  reviewed_data?: Record<string, unknown>;
}) {
  const { data } = await api.put<ReviewResponse>(`/review/${input.documentId}`, {
    status: input.status,
    reviewer_notes: input.reviewer_notes,
    reviewed_data: input.reviewed_data,
  });
  return data;
}

export async function getMetadata(documentId: number) {
  const { data } = await api.get<MetadataResponse>(`/metadata/${documentId}`);
  return data;
}

export function fileUrl(documentId: number) {
  return `${API_BASE_URL}/documents/${documentId}/file`;
}

export function exportUrl(format: "json" | "csv", documentId?: number | null) {
  const suffix = documentId ? `?document_id=${documentId}` : "";
  return `${API_BASE_URL}/export/${format}${suffix}`;
}
