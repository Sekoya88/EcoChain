"use client";

import type { CarbonReport } from "./api";

const STORAGE_KEY = "ecochain-analyzed-documents";

export interface StoredDocument {
  id: string;
  filename: string;
  report: CarbonReport;
  analyzedAt: string;
}

function loadFromStorage(): StoredDocument[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as StoredDocument[];
  } catch {
    return [];
  }
}

function saveToStorage(docs: StoredDocument[]) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(docs.slice(-50)));
  } catch {
    // ignore
  }
}

export function getAnalyzedDocuments(): StoredDocument[] {
  return loadFromStorage();
}

export function addAnalyzedDocument(
  filename: string,
  report: CarbonReport
): StoredDocument {
  const docs = loadFromStorage();
  const doc: StoredDocument = {
    id: report.document_id,
    filename,
    report,
    analyzedAt: new Date().toISOString(),
  };
  docs.unshift(doc);
  saveToStorage(docs);
  return doc;
}

export function addAnalyzedDocumentsFromBatch(
  filenames: string[],
  reports: CarbonReport[]
): StoredDocument[] {
  const docs = loadFromStorage();
  const newDocs: StoredDocument[] = reports.map((report, i) => ({
    id: report.document_id,
    filename: filenames[i] ?? `document_${i + 1}`,
    report,
    analyzedAt: new Date().toISOString(),
  }));
  newDocs.forEach((d) => docs.unshift(d));
  saveToStorage(docs);
  return newDocs;
}
