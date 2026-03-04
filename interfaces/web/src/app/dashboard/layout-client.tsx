"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Sidebar,
  SidebarBody,
  SidebarLink,
  EcoChainLogo,
} from "@/components/ui/sidebar-kodama";
import { LayoutDashboard, FileText, Settings } from "lucide-react";

const links = [
  { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard className="h-5 w-5 flex-shrink-0" /> },
  { label: "Documents", href: "/dashboard/documents", icon: <FileText className="h-5 w-5 flex-shrink-0" /> },
  { label: "Settings", href: "/dashboard/settings", icon: <Settings className="h-5 w-5 flex-shrink-0" /> },
];

export function DashboardClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            <EcoChainLogo collapsed={!open} />
            <div className="mt-8 flex flex-col gap-2">
              {links.map((link, i) => (
                <SidebarLink key={i} link={link} />
              ))}
            </div>
          </div>
          <Link
            href="/"
            className="text-xs text-[var(--muted-foreground)] hover:text-[var(--primary)]"
          >
            ← Back to home
          </Link>
        </SidebarBody>
      </Sidebar>
      <main className="flex-1 overflow-auto md:ml-0">{children}</main>
    </div>
  );
}
