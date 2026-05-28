"use client";

import * as React from "react";
import { Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSettingsPanelActions } from "@/components/settings/settings-panel-actions";
import { settingsButtonClassName } from "@/components/settings/settings-controls";

export function LightragDomainsHeaderActions() {
  const { lightragDomains } = useSettingsPanelActions();
  if (!lightragDomains) return null;

  const { onRefresh, onToggleCreate, createOpen, loading } = lightragDomains;

  return (
    <div className="ml-auto flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={onRefresh}
        disabled={loading}
        className={`${settingsButtonClassName} px-4`}
      >
        <RefreshCw className={`mr-2 size-3.5 ${loading ? "animate-spin" : ""}`} />
        Refresh
      </Button>
      <Button size="sm" onClick={onToggleCreate} className={`${settingsButtonClassName} px-4`}>
        <Plus className="mr-2 size-3.5" />
        {createOpen ? "Hide create" : "+ Create"}
      </Button>
    </div>
  );
}
