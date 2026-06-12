import React, { createContext, useContext, useState, useEffect } from "react";

export type UserRole = "Analyst" | "Manager" | "Governance Lead";

type RoleContextType = {
  role: UserRole;
  setRole: (role: UserRole) => void;
  isAnalyst: boolean;
  isManager: boolean;
  isGovLead: boolean;
  canPerform: (action: string) => boolean;
};

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<UserRole>(() => {
    const saved = localStorage.getItem("user_role");
    if (saved === "Analyst" || saved === "Manager" || saved === "Governance Lead") {
      return saved as UserRole;
    }
    return "Analyst";
  });

  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    localStorage.setItem("user_role", newRole);
    // Reload components to make sure React Query cache is refreshed or queries use the new header
    window.location.reload();
  };

  const isAnalyst = role === "Analyst";
  const isManager = role === "Manager";
  const isGovLead = role === "Governance Lead";

  const canPerform = (action: string): boolean => {
    switch (action) {
      case "upload":
      case "view_reports":
      case "view_escalations":
        return true; // Everyone can do these
      case "review_report":
      case "approve_report":
      case "escalate_report":
      case "assign_report":
        return isManager || isGovLead; // Manager/Lead only
      case "route_escalation":
        return isManager || isGovLead;
      case "assign_escalation":
      case "resolve_escalation":
      case "close_escalation":
      case "override_decision":
        return isGovLead; // Gov Lead only
      default:
        return false;
    }
  };

  return (
    <RoleContext.Provider value={{ role, setRole, isAnalyst, isManager, isGovLead, canPerform }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (context === undefined) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
