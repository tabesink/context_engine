import * as React from "react";
import { cn } from "@/lib/utils";

function Breadcrumb({ className, ...props }: React.ComponentProps<"nav">) {
  return <nav aria-label="breadcrumb" className={cn("", className)} {...props} />;
}

function BreadcrumbList({ className, ...props }: React.ComponentProps<"ol">) {
  return <ol className={cn("flex items-center gap-1.5 text-sm text-muted-foreground", className)} {...props} />;
}

function BreadcrumbItem({ className, ...props }: React.ComponentProps<"li">) {
  return <li className={cn("inline-flex items-center gap-1.5", className)} {...props} />;
}

function BreadcrumbLink({ className, ...props }: React.ComponentProps<"a">) {
  return <a className={cn("hover:text-foreground transition-colors", className)} {...props} />;
}

function BreadcrumbPage({ className, ...props }: React.ComponentProps<"span">) {
  return <span aria-current="page" className={cn("font-medium text-foreground", className)} {...props} />;
}

function BreadcrumbSeparator({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span aria-hidden="true" className={cn("text-muted-foreground/70", className)} {...props}>
      /
    </span>
  );
}

export { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator };
