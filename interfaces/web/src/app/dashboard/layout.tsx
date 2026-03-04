export const dynamic = "force-dynamic";

import { DashboardClientLayout } from "./layout-client";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardClientLayout>{children}</DashboardClientLayout>;
}
