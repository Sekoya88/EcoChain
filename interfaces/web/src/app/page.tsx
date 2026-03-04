"use client";

import Link from "next/link";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { Leaf, FileText, BarChart3, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex flex-col overflow-hidden min-h-screen bg-[var(--background)]">
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <div className="h-8 w-9 rounded-lg bg-[var(--primary)] flex items-center justify-center">
            <Leaf className="h-4 w-4 text-[var(--primary-foreground)]" />
          </div>
          <span className="font-semibold text-[var(--foreground)]">EcoChain</span>
        </div>
        <nav className="flex gap-3">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">Dashboard</Button>
          </Link>
          <Link href="/dashboard">
            <Button size="sm">Get Started</Button>
          </Link>
        </nav>
      </header>

      <main>
        <section className="pb-[400px] pt-[140px]">
          <ContainerScroll
            titleComponent={
              <>
                <h1 className="text-4xl md:text-5xl font-semibold text-[var(--foreground)]">
                  Supply Chain
                  <br />
                  <span className="text-4xl md:text-[5rem] font-bold mt-1 leading-none text-[var(--primary)]">
                    Carbon Optimizer
                  </span>
                </h1>
                <p className="text-[var(--muted-foreground)] mt-6 text-lg max-w-2xl mx-auto">
                  Scope 3 Multi-Agent Analysis — AGNO + Gemini 2.5 Flash. Analysez vos documents logistiques, calculez les émissions CO2 et obtenez des recommandations actionnables.
                </p>
                <Link href="/dashboard" className="inline-block mt-8">
                  <Button size="lg" className="bg-[var(--primary)] hover:bg-[var(--accent)] text-[var(--primary-foreground)]">
                    Analyser un document
                  </Button>
                </Link>
              </>
            }
          >
            <Image
              src="/sekoya.jpg"
              alt="Forêt durable — Kodama Grove"
              height={720}
              width={1400}
              className="mx-auto rounded-2xl object-cover h-full object-center"
              unoptimized
            />
          </ContainerScroll>
        </section>

        <section className="py-24 px-6 max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-[var(--foreground)] text-center mb-12">
            Comment ça marche
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              <FileText className="h-10 w-10 text-[var(--primary)] mb-4" />
              <h3 className="font-semibold text-[var(--foreground)] mb-2">1. Uploadez</h3>
              <p className="text-sm text-[var(--muted-foreground)]">
                Factures, bons de livraison, documents logistiques au format PDF.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              <BarChart3 className="h-10 w-10 text-[var(--primary)] mb-4" />
              <h3 className="font-semibold text-[var(--foreground)] mb-2">2. Analysez</h3>
              <p className="text-sm text-[var(--muted-foreground)]">
                Extraction, validation et calcul CO2 automatique via agents IA.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              <Sparkles className="h-10 w-10 text-[var(--primary)] mb-4" />
              <h3 className="font-semibold text-[var(--foreground)] mb-2">3. Optimisez</h3>
              <p className="text-sm text-[var(--muted-foreground)]">
                Recommandations personnalisées pour réduire votre empreinte carbone.
              </p>
            </div>
          </div>
          <div className="text-center mt-12">
            <Link href="/dashboard">
              <Button variant="outline" className="border-[var(--primary)] text-[var(--primary)]">
                Accéder au Dashboard
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="py-8 border-t border-[var(--border)] text-center text-sm text-[var(--muted-foreground)]">
        EcoChain AI — Supply Chain Carbon Footprint Optimization
      </footer>
    </div>
  );
}
