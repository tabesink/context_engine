"use client";

import * as React from "react";

export type LightragDomainsHeaderActions = {
  onRefresh: () => void;
  onToggleCreate: () => void;
  createOpen: boolean;
  loading: boolean;
};

type ContextValue = {
  lightragDomains: LightragDomainsHeaderActions | null;
  setLightragDomains: (actions: LightragDomainsHeaderActions | null) => void;
};

const SettingsPanelActionsContext = React.createContext<ContextValue | null>(null);

export function SettingsPanelActionsProvider({ children }: { children: React.ReactNode }) {
  const [lightragDomains, setLightragDomains] = React.useState<LightragDomainsHeaderActions | null>(null);
  const value = React.useMemo(() => ({ lightragDomains, setLightragDomains }), [lightragDomains]);
  return <SettingsPanelActionsContext.Provider value={value}>{children}</SettingsPanelActionsContext.Provider>;
}

export function useSettingsPanelActions() {
  const context = React.useContext(SettingsPanelActionsContext);
  if (!context) {
    throw new Error("useSettingsPanelActions must be used within SettingsPanelActionsProvider");
  }
  return context;
}

export function useRegisterLightragDomainsActions(actions: LightragDomainsHeaderActions | null) {
  const { setLightragDomains } = useSettingsPanelActions();
  React.useEffect(() => {
    setLightragDomains(actions);
    return () => setLightragDomains(null);
  }, [actions, setLightragDomains]);
}
