"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as React from "react";
import { Bot, FileText, HardDrive, ShieldAlert, UserRound, Workflow, X } from "lucide-react";
import { AIModelSettingsPanel } from "@/components/settings/panels/AIModelSettingsPanel";
import { DocumentsProcessingSettingsPanel } from "@/components/settings/panels/DocumentsProcessingSettingsPanel";
import { JobsSettingsPanel } from "@/components/settings/panels/JobsSettingsPanel";
import { SectionCard } from "@/components/surfaces/SectionCard";
import { SurfaceHeader } from "@/components/surfaces/SurfaceHeader";
import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
} from "@/components/ui/sidebar";
import { LightragDomainsHeaderActions } from "@/components/settings/LightragDomainsHeaderActions";
import { AccountSettingsPanel } from "@/components/settings/panels/AccountSettingsPanel";
import { KnowledgeGraphSettingsPanel } from "@/components/settings/panels/KnowledgeGraphSettingsPanel";
import { SettingsPanelActionsProvider } from "@/components/settings/settings-panel-actions";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import {
  closeSettingsDialog,
  setSettingsDialogOpen,
  setSettingsDialogRoute,
  useSettingsDialogStore,
  type SettingsRoute,
} from "@/stores/settings-dialog-store";
import { settingsDialogShellClassName } from "@/components/settings/settings-controls";
import type { ComponentType } from "react";

const ROUTES: Array<{ id: SettingsRoute; label: string; icon: ComponentType<{ className?: string }>; adminOnly?: boolean }> = [
  { id: "account", label: "Account", icon: UserRound },
  { id: "provider", label: "Provider", icon: Bot, adminOnly: true },
  { id: "lightrag-domains", label: "LightRAG Domains", icon: Workflow, adminOnly: true },
  { id: "documents", label: "Documents", icon: FileText, adminOnly: true },
  { id: "jobs", label: "Jobs", icon: HardDrive, adminOnly: true },
  { id: "system", label: "System", icon: ShieldAlert, adminOnly: true },
];

function PlaceholderPanel({ title, text }: { title: string; text: string }) {
  return (
    <SectionCard title={title} description={text}>
      <div className="h-1" />
    </SectionCard>
  );
}

export function SettingsDialog() {
  const isOpen = useSettingsDialogStore((state) => state.isOpen);
  const route = useSettingsDialogStore((state) => state.route);
  const isAdmin = useAuthStore(selectIsAdmin);
  const activeRouteLabel = ROUTES.find((item) => item.id === route)?.label ?? "Account";
  const isBlockedRoute = Boolean(ROUTES.find((item) => item.id === route)?.adminOnly && !isAdmin);
  const showRouteHeader = route !== "lightrag-domains" && route !== "documents" && route !== "provider";

  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={setSettingsDialogOpen}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-background/70 backdrop-blur-[1px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 dark:bg-background/60" />
        <DialogPrimitive.Content className={settingsDialogShellClassName}>
          <DialogPrimitive.Title className="sr-only">Settings</DialogPrimitive.Title>
          <SettingsPanelActionsProvider>
          <SidebarProvider className="h-full min-h-0">
            <Sidebar className="w-[220px] border-r border-border bg-background">
              <SidebarHeader>
                <div className="mb-2 flex items-center gap-2 px-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Close settings"
                  onClick={closeSettingsDialog}
                  className="rounded-md text-foreground hover:bg-muted"
                >
                  <X className="size-4" />
                </Button>
                <div>
                  <p className="text-sm font-medium text-foreground">Settings</p>
                  <p className="text-[11px] text-muted-foreground">Workspace controls</p>
                </div>
              </div>
              </SidebarHeader>
              <SidebarContent>
                <SidebarGroup>
                  <SidebarGroupLabel>Workspace</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu aria-label="Settings sections">
                      {ROUTES.filter((item) => !item.adminOnly).map((item) => {
                        const Icon = item.icon;
                        const active = route === item.id;
                        return (
                          <SidebarMenuItem key={item.id}>
                            <SidebarMenuButton
                              type="button"
                              isActive={active}
                              onClick={() => setSettingsDialogRoute(item.id)}
                              aria-current={active ? "page" : undefined}
                            >
                              <Icon className="size-4 shrink-0" />
                              <span className="truncate">{item.label}</span>
                            </SidebarMenuButton>
                          </SidebarMenuItem>
                        );
                      })}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
                <SidebarGroup>
                  <SidebarGroupLabel>Administration</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu aria-label="Admin sections">
                      {ROUTES.filter((item) => item.adminOnly).map((item) => {
                        const Icon = item.icon;
                        const active = route === item.id;
                        const blocked = Boolean(item.adminOnly && !isAdmin);
                        return (
                          <SidebarMenuItem key={item.id}>
                            <SidebarMenuButton
                              type="button"
                              isActive={active}
                              onClick={() => (blocked ? undefined : setSettingsDialogRoute(item.id))}
                              disabled={blocked}
                              className={blocked ? "cursor-not-allowed opacity-45 hover:bg-transparent" : ""}
                              aria-current={active ? "page" : undefined}
                            >
                              <Icon className="size-4 shrink-0" />
                              <span className="truncate">{item.label}</span>
                            </SidebarMenuButton>
                          </SidebarMenuItem>
                        );
                      })}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              </SidebarContent>
              <SidebarRail />
              {!isAdmin ? (
                <p className="mt-3 rounded-lg border border-border bg-muted/30 px-2.5 py-2 text-xs leading-5 text-muted-foreground">
                  Admin sections are shown for visibility and stay disabled for your role.
                </p>
              ) : null}
            </Sidebar>

            <SidebarInset className="flex min-h-0 flex-1 flex-col overflow-hidden">
              <header className="flex h-11 shrink-0 items-center gap-2 border-b border-border px-5">
                <Breadcrumb>
                  <BreadcrumbList>
                    <BreadcrumbItem className="hidden md:block">
                      <span>Settings</span>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator className="hidden md:block" />
                    <BreadcrumbItem>
                      <BreadcrumbPage>{activeRouteLabel}</BreadcrumbPage>
                    </BreadcrumbItem>
                  </BreadcrumbList>
                </Breadcrumb>
                {route === "lightrag-domains" && !isBlockedRoute ? <LightragDomainsHeaderActions /> : null}
              </header>
              <section className="min-h-0 flex-1 overflow-y-auto px-8 py-6">
              {showRouteHeader ? (
                <SurfaceHeader
                  title={activeRouteLabel}
                  description={isBlockedRoute ? "Admin access is required for this section." : undefined}
                  className="mb-6 border-b border-border pb-4"
                />
              ) : null}
              {route === "account" ? <AccountSettingsPanel embedded /> : null}
              {route === "provider" ? (isBlockedRoute ? <PlaceholderPanel title="Provider" text="Admin access is required." /> : <AIModelSettingsPanel />) : null}
              {route === "lightrag-domains" ? (isBlockedRoute ? <PlaceholderPanel title="LightRAG Domains" text="Admin access is required." /> : <KnowledgeGraphSettingsPanel />) : null}
              {route === "documents" ? (isBlockedRoute ? <PlaceholderPanel title="Documents" text="Admin access is required." /> : <DocumentsProcessingSettingsPanel />) : null}
              {route === "jobs" ? (isBlockedRoute ? <PlaceholderPanel title="Jobs" text="Admin access is required." /> : <JobsSettingsPanel />) : null}
              {route === "system" ? <PlaceholderPanel title="System" text="This section is reserved for admin system controls and is not wired yet." /> : null}
              </section>
            </SidebarInset>
          </SidebarProvider>
          </SettingsPanelActionsProvider>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
