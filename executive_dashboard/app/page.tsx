import DashboardShell from "@/components/dashboard-shell";
import { getDashboardConfig } from "@/lib/env";

export default function Page() {
  const config = getDashboardConfig();
  return <DashboardShell config={config} />;
}
