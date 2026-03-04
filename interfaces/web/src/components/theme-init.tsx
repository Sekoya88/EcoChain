"use client";

import { useEffect } from "react";

/** Runs once on mount to apply theme from localStorage. Prevents flash. */
export function ThemeInit() {
  useEffect(() => {
    const t = localStorage.getItem("ecochain-theme") || "dark";
    const effective =
      t === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : t;
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(effective);
  }, []);
  return null;
}
