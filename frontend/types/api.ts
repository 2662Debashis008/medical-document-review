export type DocumentCategory = "prescription" | "xray" | "lab_report";
export type FileType = "image" | "pdf" | "text";
export type ReviewStatus = "approved" | "rejected" | "needs_changes";
export type WorkflowStatus = "uploaded" | "processing" | "processed" | "failed" | "approved" | "rejected" | "needs_changes" | string;

export interface MedicalDocument {
  id: number;
  document_category: DocumentCategory;
  file_type: FileType;
  original_filename: string;
  stored_filename: string;
  storage_path: string;
  status: WorkflowStatus;
  review_status?: ReviewStatus | null;
  extraction_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  message: string;
  document_id: number;
  filename: string;
  status: string;
  processed_files: string[];
}

export interface ExtractResponse {
  document_id: number;
  extraction_id: number;
  status: string;
  extracted_data: Record<string, unknown>;
  metadata_id: number | null;
}

export interface ExtractionResponse {
  document_id: number;
  extraction_id: number;
  extracted_data: Record<string, unknown>;
}

export interface ReviewResponse {
  id: number;
  document_id: number;
  status: ReviewStatus;
  reviewer_notes?: string | null;
  reviewed_data?: Record<string, unknown> | null;
  reviewer_id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MetadataResponse {
  id: number;
  document_id: number;
  model_name?: string | null;
  model_version?: string | null;
  runtime?: string | null;
  prompt_version?: string | null;
  latency?: number | null;
  processing_time?: number | null;
  document_category?: string | null;
  file_type?: string | null;
  errors?: string | null;
  created_at?: string | null;
}
