"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

function SidebarProvider({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex h-full w-full", className)} {...props} />;
}

function Sidebar({ className, ...props }: React.ComponentProps<"aside">) {
  return <aside className={cn("w-[220px] shrink-0", className)} {...props} />;
}

function SidebarHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("px-3 py-4", className)} {...props} />;
}

function SidebarContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("px-3 pb-4", className)} {...props} />;
}

function SidebarGroup({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("mb-5", className)} {...props} />;
}

function SidebarGroupLabel({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div className={cn("mb-2 px-2 text-[11px] uppercase tracking-wide text-muted-foreground", className)} {...props} />
  );
}

function SidebarGroupContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("", className)} {...props} />;
}

function SidebarMenu({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("space-y-1", className)} {...props} />;
}

function SidebarMenuItem({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("", className)} {...props} />;
}

function SidebarMenuButton({
  className,
  isActive,
  asChild,
  ...props
}: React.ComponentProps<"button"> & { isActive?: boolean; asChild?: boolean }) {
  if (asChild) {
    const child = React.Children.only(props.children) as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, {
      className: cn(
        "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-sm transition-colors",
        isActive ? "bg-muted text-foreground" : "text-foreground hover:bg-muted/70",
        child.props.className,
        className,
      ),
    });
  }
  return (
    <button
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-sm transition-colors",
        isActive ? "bg-muted text-foreground" : "text-foreground hover:bg-muted/70",
        className,
      )}
      {...props}
    />
  );
}

function SidebarRail() {
  return null;
}

function SidebarInset({ className, ...props }: React.ComponentProps<"section">) {
  return <section className={cn("min-w-0 flex-1", className)} {...props} />;
}

function SidebarTrigger({ className, ...props }: React.ComponentProps<"button">) {
  return <button type="button" className={cn("hidden", className)} {...props} />;
}

export {
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
  SidebarTrigger,
};
