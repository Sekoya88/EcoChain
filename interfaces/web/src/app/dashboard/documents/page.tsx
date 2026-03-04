"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { FileText, Truck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { getAnalyzedDocuments, type StoredDocument } from "@/lib/documents-store";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<StoredDocument[]>([]);

  useEffect(() => {
    setDocs(getAnalyzedDocuments());
  }, []);

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto">
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-[var(--muted-foreground)] hover:text-[var(--primary)]">
          ← Retour au Dashboard
        </Link>
      </div>
      <h1 className="text-2xl font-bold text-[var(--foreground)] mb-2">
        Documents analysés
      </h1>
      <p className="text-[var(--muted-foreground)] mb-8">
        {docs.length > 0
          ? `${docs.length} document${docs.length > 1 ? "s" : ""} analysé${docs.length > 1 ? "s" : ""}`
          : "Vos documents apparaîtront ici après analyse."}
      </p>

      {docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 rounded-2xl border border-dashed border-[var(--border)] bg-[var(--card)]">
          <FileText className="h-16 w-16 text-[var(--muted-foreground)] mb-4" />
          <p className="text-[var(--muted-foreground)] text-center max-w-sm">
            Aucun document analysé. Uploadez un PDF ou sélectionnez un mock sur le Dashboard.
          </p>
          <Link href="/dashboard" className="mt-6">
            <span className="text-[var(--primary)] font-medium hover:underline">
              Aller au Dashboard →
            </span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {docs.map((doc) => (
            <Card key={doc.id} className="bg-[var(--card)] border-[var(--border)]">
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <div className="h-10 w-10 rounded-lg bg-[var(--sidebar-accent)] flex items-center justify-center flex-shrink-0">
                      <Truck className="h-5 w-5 text-[var(--primary)]" />
                    </div>
                    <div>
                      <p className="font-semibold text-[var(--foreground)]">{doc.filename}</p>
                      <p className="text-sm text-[var(--muted-foreground)] mt-0.5">
                        {(() => {
                          const s = doc.report.shipments?.[0] as { origin?: string; destination?: string } | undefined;
                          return s ? `${s.origin ?? "—"} → ${s.destination ?? "—"}` : "—";
                        })()}
                        {" · "}
                        <span className="text-[var(--primary)] font-medium">
                          {doc.report.total_co2_kg.toFixed(1)} kgCO2e
                        </span>
                      </p>
                      <p className="text-xs text-[var(--muted-foreground)] mt-1">
                        Analysé le {new Date(doc.analyzedAt).toLocaleString("fr-FR")}
                      </p>
                    </div>
                  </div>
                  <Link href="/dashboard">
                    <span className="text-sm text-[var(--primary)] hover:underline">
                      Voir détails →
                    </span>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
