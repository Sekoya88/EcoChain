"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Sun, Moon, Monitor } from "lucide-react";

export default function SettingsPage() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("dark");

  useEffect(() => {
    const stored = localStorage.getItem("ecochain-theme") as "light" | "dark" | "system" | null;
    if (stored) setTheme(stored);
    else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
    }
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const effective = theme === "system"
      ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : theme;
    root.classList.remove("light", "dark");
    root.classList.add(effective);
    localStorage.setItem("ecochain-theme", theme);
  }, [theme]);

  return (
    <div className="p-6 md:p-10 max-w-2xl mx-auto">
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-[var(--muted-foreground)] hover:text-[var(--primary)]">
          ← Retour au Dashboard
        </Link>
      </div>
      <h1 className="text-2xl font-bold text-[var(--foreground)] mb-2">
        Paramètres
      </h1>
      <p className="text-[var(--muted-foreground)] mb-8">
        Personnalisez l&apos;apparence de l&apos;application.
      </p>

      <div className="space-y-6">
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <h2 className="font-semibold text-[var(--foreground)] mb-3">Thème</h2>
          <div className="flex gap-2">
            {[
              { id: "light" as const, label: "Clair", icon: Sun },
              { id: "dark" as const, label: "Sombre", icon: Moon },
              { id: "system" as const, label: "Système", icon: Monitor },
            ].map(({ id, label, icon: IconC }) => (
              <button
                key={id}
                onClick={() => setTheme(id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                  theme === id
                    ? "border-[var(--primary)] bg-[var(--sidebar-accent)] text-[var(--primary)]"
                    : "border-[var(--border)] hover:border-[var(--muted-foreground)] text-[var(--muted-foreground)]"
                }`}
              >
                <IconC className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <h2 className="font-semibold text-[var(--foreground)] mb-3">À propos</h2>
          <p className="text-sm text-[var(--muted-foreground)]">
            EcoChain AI — Supply Chain Carbon Footprint Optimization. Thème Kodama Grove (21st.dev).
          </p>
        </div>
      </div>
    </div>
  );
}
