"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  settingsButtonClassName,
  settingsInputClassName,
  settingsSelectTriggerClassName,
} from "@/components/settings/settings-controls";
import type { AIModelProfile } from "@/types/ai-settings";

type RetrievalProfile = "precise" | "balanced" | "broad" | "custom";

const RETRIEVAL_PROFILES: Record<
  Exclude<RetrievalProfile, "custom">,
  { topK: string; chunkTopK: string; rerankTopK: string; textTokens: string; globalTokens: string; localTokens: string }
> = {
  precise: { topK: "6", chunkTopK: "6", rerankTopK: "6", textTokens: "2500", globalTokens: "2500", localTokens: "2500" },
  balanced: { topK: "10", chunkTopK: "10", rerankTopK: "10", textTokens: "4000", globalTokens: "4000", localTokens: "4000" },
  broad: { topK: "20", chunkTopK: "20", rerankTopK: "20", textTokens: "6000", globalTokens: "6000", localTokens: "6000" },
};

function embeddingProfileLabel(profile: AIModelProfile): string {
  const dims = profile.dimensions ? ` · ${profile.dimensions} dims` : "";
  return `${profile.provider} · ${profile.model}${dims}`;
}

function NumberInput({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-xs text-foreground">
        {label}
      </Label>
      <Input
        id={id}
        type="number"
        min={1}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={settingsInputClassName}
      />
    </div>
  );
}

export function CreateDomainForm({
  open,
  createBusy,
  embeddingProfiles,
  selectedEmbeddingProfileId,
  onSelectedEmbeddingProfileIdChange,
  onCancel,
  onSubmit,
}: {
  open: boolean;
  createBusy: boolean;
  embeddingProfiles: AIModelProfile[];
  selectedEmbeddingProfileId: string;
  onSelectedEmbeddingProfileIdChange: (value: string) => void;
  onCancel: () => void;
  onSubmit: (payload: {
    domainId: string;
    displayName: string;
    hostPort?: number;
    topK: number;
    chunkTopK: number;
    chunkRerankTopK: number;
    textUnitTokens: number;
    globalTokens: number;
    localTokens: number;
  }) => Promise<void>;
}) {
  const [newDomainId, setNewDomainId] = React.useState("");
  const [newDisplayName, setNewDisplayName] = React.useState("");
  const [hostPortMode, setHostPortMode] = React.useState<"auto" | "custom">("auto");
  const [newHostPort, setNewHostPort] = React.useState("");
  const [retrievalProfile, setRetrievalProfile] = React.useState<RetrievalProfile>("balanced");
  const [newTopK, setNewTopK] = React.useState("10");
  const [newChunkTopK, setNewChunkTopK] = React.useState("10");
  const [newChunkRerankTopK, setNewChunkRerankTopK] = React.useState("10");
  const [newTextUnitTokens, setNewTextUnitTokens] = React.useState("4000");
  const [newGlobalTokens, setNewGlobalTokens] = React.useState("4000");
  const [newLocalTokens, setNewLocalTokens] = React.useState("4000");
  const [advancedOpen, setAdvancedOpen] = React.useState(false);

  const applyProfileDefaults = (profile: Exclude<RetrievalProfile, "custom">) => {
    const defaults = RETRIEVAL_PROFILES[profile];
    setNewTopK(defaults.topK);
    setNewChunkTopK(defaults.chunkTopK);
    setNewChunkRerankTopK(defaults.rerankTopK);
    setNewTextUnitTokens(defaults.textTokens);
    setNewGlobalTokens(defaults.globalTokens);
    setNewLocalTokens(defaults.localTokens);
  };

  const resetForm = () => {
    setNewDomainId("");
    setNewDisplayName("");
    setHostPortMode("auto");
    setNewHostPort("");
    setRetrievalProfile("balanced");
    applyProfileDefaults("balanced");
    setAdvancedOpen(false);
  };

  if (!open) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const domainId = newDomainId.trim();
    const displayName = newDisplayName.trim();
    const hostPortRaw = hostPortMode === "custom" ? newHostPort.trim() : "";
    const parsedHostPort = hostPortRaw ? Number.parseInt(hostPortRaw, 10) : undefined;
    if (!domainId) return;

    const parsePositiveInt = (value: string) => {
      const parsed = Number.parseInt(value.trim(), 10);
      if (!Number.isInteger(parsed) || parsed < 1) return undefined;
      return parsed;
    };

    const topK = parsePositiveInt(newTopK);
    const chunkTopK = parsePositiveInt(newChunkTopK);
    const chunkRerankTopK = parsePositiveInt(newChunkRerankTopK);
    const textUnitTokens = parsePositiveInt(newTextUnitTokens);
    const globalTokens = parsePositiveInt(newGlobalTokens);
    const localTokens = parsePositiveInt(newLocalTokens);

    if (!topK || !chunkTopK || !chunkRerankTopK || !textUnitTokens || !globalTokens || !localTokens) {
      return;
    }

    try {
      await onSubmit({
        domainId,
        displayName,
        hostPort: parsedHostPort,
        topK,
        chunkTopK,
        chunkRerankTopK,
        textUnitTokens,
        globalTokens,
        localTokens,
      });
      resetForm();
    } catch {
      // Parent surfaces API errors.
    }
  };

  return (
    <Card className="gap-0 py-0 shadow-sm">
      <form onSubmit={(event) => void handleSubmit(event)}>
        <CardHeader className="border-b border-border px-5 py-4">
          <CardTitle className="text-sm">Create knowledge graph domain</CardTitle>
          <CardDescription>Create an isolated retrieval domain for documents and evidence.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-5 py-4">
          <div>
            <p className="mb-2 text-xs font-medium text-foreground">Domain identity</p>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="kg-domain-id" className="text-xs font-medium text-foreground">
                  Domain ID
                </Label>
                <Input
                  id="kg-domain-id"
                  placeholder="fatigue"
                  value={newDomainId}
                  onChange={(event) => setNewDomainId(event.target.value)}
                  className={settingsInputClassName}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-display-name" className="text-xs font-medium text-foreground">
                  Display name
                </Label>
                <Input
                  id="kg-display-name"
                  placeholder="Fatigue Manuals"
                  value={newDisplayName}
                  onChange={(event) => setNewDisplayName(event.target.value)}
                  className={settingsInputClassName}
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="kg-embedding-profile" className="text-xs font-medium text-foreground">
              Embedding model
            </Label>
            <Select value={selectedEmbeddingProfileId} onValueChange={onSelectedEmbeddingProfileIdChange}>
              <SelectTrigger id="kg-embedding-profile" className={settingsSelectTriggerClassName}>
                <SelectValue placeholder="Select embedding model" />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-border shadow-none">
                {embeddingProfiles.map((profile) => (
                  <SelectItem key={profile.id} value={profile.id}>
                    {embeddingProfileLabel(profile)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs leading-4 text-muted-foreground">
              Locked after creation. All documents in this domain share the same embedding space.
            </p>
          </div>

          <div className="space-y-2.5">
            <p className="text-xs font-medium text-foreground">Host port</p>
            <RadioGroup
              value={hostPortMode}
              onValueChange={(value) => {
                const mode = value as "auto" | "custom";
                setHostPortMode(mode);
                if (mode === "auto") setNewHostPort("");
              }}
              className="gap-2"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem value="auto" id="host-port-auto" />
                <Label htmlFor="host-port-auto" className="text-xs font-normal text-foreground">
                  Auto-assign available port
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="custom" id="host-port-custom" />
                <Label htmlFor="host-port-custom" className="text-xs font-normal text-foreground">
                  Use custom port
                </Label>
              </div>
            </RadioGroup>
            {hostPortMode === "custom" ? (
              <div className="space-y-1.5">
                <Label htmlFor="kg-host-port" className="text-xs font-medium text-foreground">
                  Custom port
                </Label>
                <Input
                  id="kg-host-port"
                  type="number"
                  min={1}
                  max={65535}
                  placeholder="9621"
                  value={newHostPort}
                  onChange={(event) => setNewHostPort(event.target.value)}
                  className={settingsInputClassName}
                />
              </div>
            ) : null}
          </div>

          <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
            <CollapsibleTrigger className="flex w-full cursor-pointer items-center justify-between border-y border-border py-3 text-xs font-medium text-foreground">
              <span>Advanced retrieval defaults</span>
              <ChevronDown className={`size-3.5 text-muted-foreground transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 pt-3">
              <p className="text-xs leading-4 text-muted-foreground">
                Tune recall and token budgets used when this domain is created.
              </p>
              <div className="space-y-1.5">
                <Label htmlFor="kg-retrieval-profile" className="text-xs text-foreground">
                  Retrieval profile
                </Label>
                <Select
                  value={retrievalProfile}
                  onValueChange={(value) => {
                    const profile = value as RetrievalProfile;
                    setRetrievalProfile(profile);
                    if (profile !== "custom") applyProfileDefaults(profile);
                  }}
                >
                  <SelectTrigger id="kg-retrieval-profile" className={settingsSelectTriggerClassName}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="rounded-xl border-border shadow-none">
                    <SelectItem value="precise">Precise</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="broad">Broad</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {retrievalProfile === "custom" ? (
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  <NumberInput id="kg-top-k" label="Top K Results" value={newTopK} onChange={setNewTopK} />
                  <NumberInput id="kg-chunk-top-k" label="Chunk Top K" value={newChunkTopK} onChange={setNewChunkTopK} />
                  <NumberInput id="kg-rerank-top-k" label="Rerank Top K" value={newChunkRerankTopK} onChange={setNewChunkRerankTopK} />
                  <NumberInput id="kg-text-unit-tokens" label="Text Unit Tokens" value={newTextUnitTokens} onChange={setNewTextUnitTokens} />
                  <NumberInput id="kg-global-tokens" label="Global Tokens" value={newGlobalTokens} onChange={setNewGlobalTokens} />
                  <NumberInput id="kg-local-tokens" label="Local Tokens" value={newLocalTokens} onChange={setNewLocalTokens} />
                </div>
              ) : null}
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
        <CardFooter className="justify-end gap-2 border-t border-border px-5 py-4">
          <Button type="button" variant="outline" className={settingsButtonClassName} onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={createBusy} className={`${settingsButtonClassName} px-5`}>
            {createBusy ? "Creating..." : "Create"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
