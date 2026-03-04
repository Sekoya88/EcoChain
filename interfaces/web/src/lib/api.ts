const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface ProcessRequest {
  document_type?: string;
  raw_content: Record<string, unknown>;
  source_filename: string;
}

export interface CarbonReport {
  document_id: string;
  shipments: Array<Record<string, unknown>>;
  emissions: Array<Record<string, unknown>>;
  total_co2_kg: number;
  mode_comparisons: Array<{ mode: string; co2_kg: number; is_current: boolean }>;
  recommendations: Array<{
    title: string;
    description: string;
    potential_saving_pct: number;
    priority: number;
    category: string;
  }>;
  validation: { is_valid: boolean; confidence_score: number };
  processing_time_ms: number;
}

export interface ProcessResponse {
  success: boolean;
  report?: CarbonReport;
  error?: { message: string; error_code: string };
}

export interface BatchProcessRequest {
  documents: ProcessRequest[];
}

export interface BatchProcessResponse {
  success: boolean;
  total_documents: number;
  successful: number;
  reports: CarbonReport[];
  total_co2_kg: number;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${BACKEND_URL}/health`);
    return r.ok;
  } catch {
    return false;
  }
}

export async function processDocument(
  payload: ProcessRequest
): Promise<ProcessResponse> {
  const r = await fetch(`${BACKEND_URL}/api/v1/documents/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return r.json();
}

export async function processBatch(
  payload: BatchProcessRequest
): Promise<BatchProcessResponse> {
  const r = await fetch(`${BACKEND_URL}/api/v1/documents/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return r.json();
}

export async function fetchEventHistory(): Promise<
  Array<{ agent: string; message: string; type: string; duration_ms?: number }>
> {
  try {
    const r = await fetch(`${BACKEND_URL}/api/v1/events/history`);
    const data = await r.json();
    return data.events ?? [];
  } catch {
    return [];
  }
}

export function getEventStreamUrl(): string {
  return `${BACKEND_URL}/api/v1/events/stream`;
}
