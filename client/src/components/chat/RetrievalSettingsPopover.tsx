"use client";

import { ArrowLeft, ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { LightRagDomain, RetrievalQueryMode, RetrievalSettings } from "@/types/chat";

type RetrievalSettingsPopoverProps = {
  settings: RetrievalSettings;
  onChange: (settings: RetrievalSettings) => void;
  lightragDomains: LightRagDomain[];
  onBack?: () => void;
};

const FIELD_DESCRIPTIONS = {
  knowledgebase: "Select from deployed healthy Knowledge Graph domains.",
  mode: "Use mix for normal chat: it combines KG retrieval with direct vector chunks. Global is relationship-driven.",
  top_k: "Number of KG items to retrieve. Represents entities in local mode and relationships in global mode.",
  chunk_top_k: "Number of text chunks to retrieve initially from vector search.",
  chunk_rerank_top_k: "Number of text chunks to keep after reranking.",
  max_token_for_text_unit: "Maximum number of tokens allowed for each retrieved text chunk.",
  max_token_for_global_context: "Maximum number of tokens allocated for relationship descriptions in global retrieval.",
  max_token_for_local_context: "Maximum number of tokens allocated for entity descriptions in local retrieval.",
};
const MODES: RetrievalQueryMode[] = ["global", "local", "hybrid", "naive", "mix"];

export function RetrievalSettingsPopover({
  settings,
  onChange,
  lightragDomains,
  onBack,
}: RetrievalSettingsPopoverProps) {
  const healthyDomains = lightragDomains.filter((domain) => domain.is_healthy === true);
  const selectedDomain = healthyDomains.find((domain) => domain.port === settings.lightrag_port);

  return (
    <div className="space-y-3">
      <div>
        <div className="flex items-center gap-1">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              className="inline-flex size-7 items-center justify-center rounded-full border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              aria-label="Back to actions"
            >
              <ArrowLeft className="size-3.5" aria-hidden />
            </button>
          ) : null}
          <h2 className="text-sm font-medium text-[var(--foreground)]">Retrieval</h2>
        </div>
        <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">
          Choose which deployed Knowledge Graph to query and tune retrieval behavior for the current chat.
        </p>
      </div>

      <DomainSelect
        domains={healthyDomains}
        selectedPort={selectedDomain?.port}
        onChange={(port) => onChange({ ...settings, lightrag_port: port })}
      />

      <div className="space-y-1.5">
        <FieldLabel label="Query Mode" description={FIELD_DESCRIPTIONS.mode} />
        <Select
          value={settings.mode}
          onValueChange={(value) => onChange({ ...settings, mode: value as RetrievalQueryMode })}
        >
          <SelectTrigger className="h-9 w-full rounded-full border-[var(--border)] bg-[var(--background)] shadow-none">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="rounded-[12px] border-[var(--border)] shadow-none">
            {MODES.map((mode) => (
              <SelectItem key={mode} value={mode}>
                {toTitleCase(mode)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <details className="group rounded-[12px] border border-[var(--border)] bg-[var(--background)] px-3 py-2">
        <summary className="flex cursor-pointer list-none items-center justify-between text-xs font-medium text-[var(--foreground)]">
          <span>Advanced Retrieval</span>
          <ChevronDown className="size-3.5 text-[var(--muted-foreground)] group-open:rotate-180" />
        </summary>
        <div className="mt-2 space-y-2">
          <NumberField
            label="Top K Results"
            description={FIELD_DESCRIPTIONS.top_k}
            value={settings.top_k}
            onChange={(value) => setNumber("top_k", value, settings, onChange)}
          />
          <NumberField
            label="Chunk Top K"
            description={FIELD_DESCRIPTIONS.chunk_top_k}
            value={settings.chunk_top_k}
            onChange={(value) => setNumber("chunk_top_k", value, settings, onChange)}
          />
          <NumberField
            label="Rerank Top K"
            description={FIELD_DESCRIPTIONS.chunk_rerank_top_k}
            value={settings.chunk_rerank_top_k}
            onChange={(value) => setNumber("chunk_rerank_top_k", value, settings, onChange)}
          />
          <NumberField
            label="Text Unit Tokens"
            description={FIELD_DESCRIPTIONS.max_token_for_text_unit}
            value={settings.max_token_for_text_unit}
            onChange={(value) => setNumber("max_token_for_text_unit", value, settings, onChange)}
          />
          <NumberField
            label="Global Tokens"
            description={FIELD_DESCRIPTIONS.max_token_for_global_context}
            value={settings.max_token_for_global_context}
            onChange={(value) => setNumber("max_token_for_global_context", value, settings, onChange)}
          />
          <NumberField
            label="Local Tokens"
            description={FIELD_DESCRIPTIONS.max_token_for_local_context}
            value={settings.max_token_for_local_context}
            onChange={(value) => setNumber("max_token_for_local_context", value, settings, onChange)}
          />
        </div>
      </details>
    </div>
  );
}

type NumberSettingKey = Exclude<keyof RetrievalSettings, "lightrag_port" | "mode" | "ids">;

type DomainSelectProps = {
  domains: LightRagDomain[];
  selectedPort?: number;
  onChange: (port: number) => void;
};

function DomainSelect({ domains, selectedPort, onChange }: DomainSelectProps) {
  if (domains.length === 0) {
    return (
      <div className="space-y-1.5">
        <FieldLabel label="Knowledge Graph" description={FIELD_DESCRIPTIONS.knowledgebase} />
        <div className="rounded-[12px] border border-[var(--border)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
          No deployed healthy Knowledge Graphs are available.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <FieldLabel label="Knowledge Graph" description={FIELD_DESCRIPTIONS.knowledgebase} />
      <Select value={selectedPort ? String(selectedPort) : undefined} onValueChange={(value) => onChange(Number(value))}>
        <SelectTrigger className="h-9 w-full rounded-full border-[var(--border)] bg-[var(--background)] shadow-none">
          <SelectValue placeholder="Choose a deployed knowledge graph" />
        </SelectTrigger>
        <SelectContent className="rounded-[12px] border-[var(--border)] shadow-none">
          {domains.map((domain) => (
            <SelectItem key={domain.domain_id} value={String(domain.port)}>
              {domain.workspace} ({domain.port})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

type NumberFieldProps = {
  label: string;
  description: string;
  value?: number;
  onChange: (value: string) => void;
};

function NumberField({ label, description, value, onChange }: NumberFieldProps) {
  return (
    <div className="space-y-1.5">
      <FieldLabel label={label} description={description} />
      <Input
        type="number"
        min={1}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-full border-[var(--border)] bg-[var(--background)] text-xs shadow-none"
      />
    </div>
  );
}

type FieldLabelProps = {
  label: string;
  description: string;
};

function FieldLabel({ label, description }: FieldLabelProps) {
  return (
    <Label className="text-xs text-[var(--foreground)]" title={description}>
      {label}
    </Label>
  );
}

function setNumber(
  key: NumberSettingKey,
  value: string,
  settings: RetrievalSettings,
  onChange: (settings: RetrievalSettings) => void,
) {
  const parsed = parsePositiveInteger(value);
  onChange({ ...settings, [key]: parsed });
}

function parsePositiveInteger(value: string) {
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

function toTitleCase(value: string) {
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}
