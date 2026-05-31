"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { AppSideRail } from "@/components/layout/AppSideRail";

type AppPageFrameProps = {
  children: ReactNode;
  contentClassName?: string;
};

export function AppPageFrame({ children, contentClassName = "" }: AppPageFrameProps) {
  const pathname = usePathname();
  const showRail = !pathname.startsWith("/settings");

  return (
    <section className="flex min-h-screen flex-1 p-5">
      <div className="relative flex h-[calc(100vh-2.5rem)] min-h-[540px] w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--background)]">
        {showRail ? <AppSideRail /> : null}
        <div className={`h-full min-w-0 flex-1 ${contentClassName}`}>{children}</div>
      </div>
    </section>
  );
}
