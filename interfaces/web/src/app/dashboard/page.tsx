"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Loader } from "@/components/ui/loader";
import { PrismFluxLoader } from "@/components/ui/prism-flux-loader";
import {
  checkHealth,
  processDocument,
  processBatch,
  fetchEventHistory,
  getEventStreamUrl,
  type ProcessResponse,
  type BatchProcessResponse,
  type CarbonReport,
} from "@/lib/api";
// PDF extract loaded dynamically to avoid SSR issues with pdfjs
import { MOCK_DOCUMENTS } from "@/data/mock-documents";
import { addAnalyzedDocument, addAnalyzedDocumentsFromBatch } from "@/lib/documents-store";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";

const PIPELINE_STEPS = ["Extract", "Validate", "Calculate", "Recommend"];

const COLORS = {
  accent: "#5a9c5a",
  current: "#c9a227",
  other: "#3d5c3d",
  rose: "#c75d5d",
};

export default function DashboardPage() {
  const [backendOk, setBackendOk] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("Processing");
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<ProcessResponse | BatchProcessResponse | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [selectedDoc, setSelectedDoc] = useState(0);
  const [logs, setLogs] = useState<Array<{ agent: string; message: string; type: string }>>([]);
  const [batchMode, setBatchMode] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const checkBackend = useCallback(async () => {
    const ok = await checkHealth();
    setBackendOk(ok);
    if (ok) {
      const events = await fetchEventHistory();
      setLogs(events);
    }
  }, []);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length) setPdfFile(accepted[0]!);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    onDropAccepted: onDrop,
  });

  const runAnalysis = async () => {
    setResult(null);
    setLoading(true);
    setStep(0);
    setLogs([]);

    // SSE stream: affiche les logs des agents en temps réel
    const url = getEventStreamUrl();
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as { type?: string; agent?: string; message?: string };
        if (data.type === "heartbeat") return;
        setLogs((prev) => [
          ...prev,
          {
            agent: data.agent ?? "system",
            message: data.message ?? "",
            type: data.type ?? "info",
          },
        ]);
      } catch {
        /* ignore parse errors */
      }
    };

    try {
      setStep(1);
      setLoadingStatus("Extracting");

      if (pdfFile) {
        const { extractTextFromPdf } = await import("@/lib/pdf-extract");
        const text = await extractTextFromPdf(pdfFile);
        const payload = {
          document_type: "invoice",
          raw_content: { raw_text: text },
          source_filename: pdfFile.name,
        };
        const res = await processDocument(payload);
        setResult(res);
        if (res.success && res.report) {
          addAnalyzedDocument(pdfFile.name, res.report);
        }
      } else if (batchMode) {
        setLoadingStatus("Batch processing");
        const payload = {
          documents: MOCK_DOCUMENTS.map((d) => ({
            document_type: d.document_type,
            raw_content: d.raw_content,
            source_filename: d.source_filename,
          })),
        };
        const res = await processBatch(payload);
        setResult(res);
        if (res.success && res.reports?.length) {
          addAnalyzedDocumentsFromBatch(
            MOCK_DOCUMENTS.map((d) => d.source_filename),
            res.reports
          );
        }
      } else {
        const doc = MOCK_DOCUMENTS[selectedDoc]!;
        const payload = {
          document_type: doc.document_type,
          raw_content: doc.raw_content,
          source_filename: doc.source_filename,
        };
        const res = await processDocument(payload);
        setResult(res);
        if (res.success && res.report) {
          addAnalyzedDocument(doc.source_filename, res.report);
        }
      }

      setStep(4);
    } catch (e) {
      setResult({
        success: false,
        error: { message: String(e), error_code: "CLIENT_ERROR" },
      } as ProcessResponse);
    } finally {
      es.close();
      eventSourceRef.current = null;
      setLoading(false);
    }
  };

  const report = result && "report" in result ? result.report : null;
  const batchReports = result && "reports" in result ? result.reports : [];
  const hasReport = report || batchReports.length > 0;

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--foreground)]">
          EcoChain AI
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          Supply Chain Carbon Optimizer — Scope 3 Multi-Agent Analysis
        </p>
        <div className="flex items-center gap-2 mt-2">
          <span
            className={`w-2 h-2 rounded-full ${backendOk ? "bg-[var(--primary)] animate-pulse" : "bg-[var(--destructive)]"}`}
          />
          <span className="text-xs text-[var(--muted-foreground)]">
            Backend: {backendOk ? "Connected" : "Offline"} · AGNO + Gemini 2.5
          </span>
        </div>
      </header>

      <div className="grid md:grid-cols-3 gap-6">
        <aside className="space-y-4">
          <Card className="bg-[var(--card)] border-[var(--border)]">
            <CardHeader className="pb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Upload PDF
              </h3>
            </CardHeader>
            <CardContent>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? "border-[var(--primary)] bg-[var(--sidebar-accent)]"
                    : "border-[var(--border)] hover:border-[var(--primary)]/50 hover:bg-[var(--card-solid)]"
                }`}
              >
                <input {...getInputProps()} />
                <p className="text-sm text-[var(--muted-foreground)]">
                  {pdfFile ? pdfFile.name : "Drag & drop or browse"}
                </p>
              </div>
              {pdfFile && (
                <Button
                  className="w-full mt-3"
                  onClick={() => runAnalysis()}
                  disabled={loading}
                >
                  Analyze Uploaded PDF
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[var(--card)] border-[var(--border)]">
            <CardHeader className="pb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Mock Documents
              </h3>
            </CardHeader>
            <CardContent>
              <select
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--card-solid)] px-3 py-2 text-sm text-[var(--foreground)]"
                value={selectedDoc}
                onChange={(e) => setSelectedDoc(Number(e.target.value))}
              >
                {MOCK_DOCUMENTS.map((d, i) => (
                  <option key={i} value={i}>
                    {d.source_filename}
                  </option>
                ))}
              </select>
              <div className="flex gap-2 mt-3">
                <Button
                  variant="outline"
                  className="flex-1 border-[var(--border)]"
                  onClick={() => {
                    setBatchMode(false);
                    setPdfFile(null);
                    setTimeout(runAnalysis, 0);
                  }}
                  disabled={loading}
                >
                  Analyze One
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-[var(--border)]"
                  onClick={() => {
                    setBatchMode(true);
                    setPdfFile(null);
                    setTimeout(runAnalysis, 0);
                  }}
                  disabled={loading}
                >
                  Batch
                </Button>
              </div>
            </CardContent>
          </Card>
        </aside>

        <main className="md:col-span-2 space-y-6">
          {loading && (
            <Card className="bg-[var(--card)] border-[var(--border)]">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="flex gap-1">
                    {PIPELINE_STEPS.map((s, i) => (
                      <span
                        key={s}
                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                          i < step
                            ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                            : i === step
                              ? "border-2 border-[var(--primary)] text-[var(--primary)]"
                              : "bg-[var(--muted)] text-[var(--muted-foreground)]"
                        }`}
                      >
                        {i < step ? "✓" : i + 1}
                      </span>
                    ))}
                  </div>
                  <PrismFluxLoader currentStatus={loadingStatus} size={30} compact />
                </div>
              </CardContent>
            </Card>
          )}

          {!loading && hasReport && (
            <>
              <div className="flex gap-2 flex-wrap">
                {PIPELINE_STEPS.map((s, i) => (
                  <span
                    key={s}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold bg-[var(--primary)] text-[var(--primary-foreground)]"
                  >
                    ✓
                  </span>
                ))}
              </div>

              {report && <ReportView report={report} />}
              {batchReports.length > 0 && (
                <BatchReportView reports={batchReports} />
              )}
            </>
          )}

          {!loading && result && !result.success && "error" in result && (
            <Card className="bg-[var(--card)] border-[var(--destructive)]">
              <CardContent className="pt-6 text-[var(--destructive)]">
                {result.error?.message}
              </CardContent>
            </Card>
          )}

          {!loading && !result && (
            <Card className="bg-[var(--card)] border-[var(--border)]">
              <CardContent className="py-16 text-center text-[var(--muted-foreground)]">
                Select a document or upload a PDF, then click Analyze.
              </CardContent>
            </Card>
          )}

          {(loading || logs.length > 0) && (
            <Card className="bg-[var(--card)] border-[var(--border)]">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-[var(--muted-foreground)]">
                    Agent Activity Log
                  </h3>
                  {loading && (
                    <Loader
                      variant="terminal"
                      size="sm"
                      className="text-[var(--primary)]"
                    />
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="max-h-64 overflow-y-auto font-mono text-xs space-y-1">
                  {logs.slice(-20).map((log, i) => (
                    <div
                      key={i}
                      className={`py-1 ${log.type === "error" ? "text-[var(--destructive)]" : "text-[var(--muted-foreground)]"}`}
                    >
                      <span className="text-[var(--primary)]">[{log.agent}]</span>{" "}
                      {log.message}
                    </div>
                  ))}
                  {loading && logs.length === 0 && (
                    <div className="text-[var(--muted-foreground)] py-4 flex items-center gap-2">
                      <Loader variant="loading-dots" text="Waiting for agents" size="sm" />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}

function ReportView({ report }: { report: CarbonReport }) {
  const comparisons = report.mode_comparisons ?? [];
  const currentMode = comparisons.find((c) => c.is_current);
  const chartData = comparisons.map((c) => ({
    name: c.mode.charAt(0).toUpperCase() + c.mode.slice(1),
    value: Math.round(c.co2_kg),
    isCurrent: c.is_current,
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total CO2"
          value={`${report.total_co2_kg.toFixed(1)} kgCO2e`}
          accent
        />
        <MetricCard
          label="Shipments"
          value={String(report.shipments?.length ?? 0)}
        />
        <MetricCard
          label="Confidence"
          value={`${report.validation?.confidence_score ?? 0}%`}
        />
        <MetricCard
          label="Processing"
          value={`${report.processing_time_ms?.toFixed(0) ?? 0} ms`}
        />
      </div>

      {chartData.length > 0 && (
        <Card className="bg-[var(--card)] border-[var(--border)] overflow-hidden">
          <CardHeader>
            <h3 className="text-sm font-semibold">
              Comparaison modale — Même trajet, émissions selon le mode
            </h3>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">
              Simulation : si vous aviez utilisé chaque mode pour ce document (même poids, même distance).
              {currentMode && (
                <span className="block mt-1 text-[var(--primary)]">
                  Votre mode actuel : <strong>{currentMode.mode.charAt(0).toUpperCase() + currentMode.mode.slice(1)}</strong>
                </span>
              )}
            </p>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="flex items-center gap-4 mb-2 text-[10px] text-[var(--muted-foreground)]">
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-2 rounded-sm" style={{ background: COLORS.current }} /> Mode actuel
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-2 rounded-sm" style={{ background: COLORS.accent }} /> Mode le moins émetteur
              </span>
            </div>
            <div className="h-64 overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 24, right: 48 }}>
                  <XAxis type="number" stroke="var(--muted-foreground)" unit=" kg" />
                  <YAxis dataKey="name" type="category" stroke="var(--muted-foreground)" width={70} tick={{ fontSize: 11 }} />
                  <Bar dataKey="value" radius={4} maxBarSize={28}>
                    <LabelList dataKey="value" position="right" formatter={(v: number) => `${v} kg`} fill="var(--muted-foreground)" fontSize={10} />
                    {chartData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={
                          entry.isCurrent
                            ? COLORS.current
                            : entry.value === Math.min(...chartData.map((d) => d.value))
                              ? COLORS.accent
                              : COLORS.other
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {report.recommendations?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--muted-foreground)] mb-3">
            Recommendations
          </h3>
          <div className="space-y-2">
            {report.recommendations.map((rec, i) => (
              <Card
                key={i}
                className="bg-[var(--card)] border-[var(--border)] border-l-4 border-l-[var(--primary)]"
              >
                <CardContent className="py-3">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <p className="text-xs text-[var(--primary)] uppercase">
                        {rec.category.replace(/_/g, " ")} · P{rec.priority}
                      </p>
                      <p className="font-semibold">{rec.title}</p>
                      <p className="text-sm text-[var(--muted-foreground)]">
                        {rec.description}
                      </p>
                    </div>
                    <span className="text-lg font-bold text-[var(--primary)] whitespace-nowrap">
                      -{rec.potential_saving_pct.toFixed(0)}%
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BatchReportView({ reports }: { reports: CarbonReport[] }) {
  const totalCo2 = reports.reduce((s, r) => s + r.total_co2_kg, 0);
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="Documents" value={String(reports.length)} />
        <MetricCard label="Successful" value={String(reports.filter((r) => r.total_co2_kg > 0).length)} />
        <MetricCard label="Total CO2" value={`${totalCo2.toFixed(1)} kgCO2e`} accent />
      </div>
      <div className="space-y-2">
        {reports.map((r, i) => (
          <Card key={i} className="bg-[var(--card)] border-[var(--border)]">
            <CardContent className="py-3 flex justify-between items-center">
              <span>Document {i + 1}</span>
              <span className="font-semibold text-[var(--primary)]">
                {r.total_co2_kg.toFixed(1)} kgCO2e
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <Card className="bg-[var(--card)] border-[var(--border)]">
      <CardContent className="pt-4">
        <p className="text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
          {label}
        </p>
        <p
          className={`text-xl font-bold mt-1 ${accent ? "text-[var(--primary)]" : "text-[var(--foreground)]"}`}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
