"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowUp, ChevronRight, Plus, Upload, Workflow } from "lucide-react";
import { RetrievalSettingsPopover } from "@/components/chat/RetrievalSettingsPopover";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import { openSettingsDialog } from "@/stores/settings-dialog-store";
import type { LightRagDomain, RetrievalSettings } from "@/types/chat";

type ChatComposerProps = {
  disabled?: boolean;
  busy?: boolean;
  placeholder?: string;
  onSubmit: (content: string) => void | Promise<void>;
  retrievalSettings: RetrievalSettings;
  onRetrievalSettingsChange: (settings: RetrievalSettings) => void;
  lightragDomains: LightRagDomain[];
  className?: string;
};

const MAX_HEIGHT_PX = 220;

export function ChatComposer({
  disabled,
  busy,
  placeholder = "Ask Knowledge Graph",
  onSubmit,
  retrievalSettings,
  onRetrievalSettingsChange,
  lightragDomains,
  className,
}: ChatComposerProps) {
  const [value, setValue] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [retrievalOpen, setRetrievalOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const isAdmin = useAuthStore(selectIsAdmin);

  const resize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, []);

  useEffect(() => {
    resize();
  }, [resize, value]);

  useEffect(() => {
    if (!menuOpen) {
      setRetrievalOpen(false);
    }
  }, [menuOpen]);

  const send = useCallback(async () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue("");
    await onSubmit(trimmed);
  }, [disabled, onSubmit, value]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  };

  const openUpload = useCallback(() => {
    if (!isAdmin) return;
    openSettingsDialog("knowledge-graph");
    setRetrievalOpen(false);
    setMenuOpen(false);
  }, [isAdmin]);

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center gap-2 rounded-full border border-transparent bg-[var(--muted)]/70 px-4 py-2 focus-within:bg-[var(--background)] focus-within:ring-1 focus-within:ring-[var(--border)]">
        <Popover open={menuOpen} onOpenChange={setMenuOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-full border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              aria-label="Open chat actions"
            >
              <Plus className="size-4" aria-hidden />
            </button>
          </PopoverTrigger>
          <PopoverContent
            className="max-h-[min(30rem,calc(100vh-2rem))] w-[min(20rem,calc(100vw-2rem))] rounded-[12px] border-[var(--border)] bg-[var(--background)] p-2 shadow-none"
            align="start"
            side="top"
            sideOffset={10}
          >
            <div className="space-y-1">
              {isAdmin ? (
                <button
                  type="button"
                  onClick={openUpload}
                  className="flex w-full items-center gap-2 rounded-full px-3 py-2 text-left text-sm text-[var(--foreground)] hover:bg-[var(--secondary)]"
                >
                  <Upload className="size-4 text-[var(--muted-foreground)]" aria-hidden />
                  <span>Upload</span>
                </button>
              ) : null}
              <Popover open={retrievalOpen} onOpenChange={setRetrievalOpen}>
                <PopoverTrigger asChild>
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 rounded-full px-3 py-2 text-left text-sm text-[var(--foreground)] hover:bg-[var(--secondary)]"
                  >
                    <Workflow className="size-4 text-[var(--muted-foreground)]" aria-hidden />
                    <span className="flex-1">Retrieval</span>
                    <ChevronRight className="size-3.5 text-[var(--muted-foreground)]" aria-hidden />
                  </button>
                </PopoverTrigger>
                <PopoverContent
                  className="max-h-[min(30rem,calc(100vh-2rem))] w-[min(20rem,calc(100vw-2rem))] overflow-y-auto rounded-[12px] border-[var(--border)] bg-[var(--background)] p-2 shadow-none"
                  align="end"
                  side="right"
                  sideOffset={-8}
                >
                  <RetrievalSettingsPopover
                    settings={retrievalSettings}
                    onChange={onRetrievalSettingsChange}
                    lightragDomains={lightragDomains}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </PopoverContent>
        </Popover>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="max-h-48 min-h-[1.5rem] flex-1 resize-none overflow-y-auto border-none bg-transparent py-1 text-base leading-relaxed text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] outline-none disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Message"
        />
        <button
          type="button"
          onClick={() => void send()}
          disabled={disabled || !value.trim()}
          className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-30"
          aria-label={busy ? "Knowledge Graph is busy" : "Send message"}
        >
          <ArrowUp className="size-4" aria-hidden />
        </button>
      </div>
    </div>
  );
}
