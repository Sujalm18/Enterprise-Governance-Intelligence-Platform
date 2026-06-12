import json
import re
from typing import List, Dict, Any, Optional

# Playbooks definitions
PLAYBOOKS = [
    {
        "name": "Vendor Dependency",
        "keywords": ["vendor", "supplier", "contractor", "third party", "third-party", "outsourcing"],
        "priority": "P1",
        "suggested_owner_role": "Manager",
        "expected_risk_reduction": "High",
        "implementation_effort": "Medium",
        "mitigations": [
            "Onboard secondary supplier",
            "Establish contingency plan",
            "Diversify contract exposure"
        ]
    },
    {
        "name": "Compliance Gap",
        "keywords": ["compliance", "regulatory", "audit", "policy gap", "legal", "gdpr", "hipaa", "soc2", "framework"],
        "priority": "P1",
        "suggested_owner_role": "Governance Lead",
        "expected_risk_reduction": "High",
        "implementation_effort": "Medium",
        "mitigations": [
            "Compliance assessment",
            "Control implementation",
            "Audit validation"
        ]
    },
    {
        "name": "Data Privacy Risk",
        "keywords": ["pii", "privacy", "personal data", "gdpr", "retention", "consent"],
        "priority": "P1",
        "suggested_owner_role": "Governance Lead",
        "expected_risk_reduction": "High",
        "implementation_effort": "Medium",
        "mitigations": [
            "Conduct Privacy Impact Assessment (PIA)",
            "Implement data minimization controls",
            "Define user consent & data retention policies"
        ]
    },
    {
        "name": "Security Control Gap",
        "keywords": ["authentication", "authorization", "access control", "security", "encryption", "vulnerability"],
        "priority": "P1",
        "suggested_owner_role": "Governance Lead",
        "expected_risk_reduction": "High",
        "implementation_effort": "Medium",
        "mitigations": [
            "Enforce multi-factor authentication (MFA)",
            "Implement role-based access control (RBAC)",
            "Conduct vulnerability scanning and remediation"
        ]
    },
    {
        "name": "AI Governance Risk",
        "keywords": ["llm", "genai", "model", "bias", "hallucination", "prompt", "ai risk"],
        "priority": "P1",
        "suggested_owner_role": "Governance Lead",
        "expected_risk_reduction": "High",
        "implementation_effort": "High",
        "mitigations": [
            "Establish AI model testing protocols",
            "Implement input/output guardrails",
            "Conduct bias and toxicity testing"
        ]
    },
    {
        "name": "Missing Policy Owner",
        "keywords": ["missing policy owner", "policy owner", "no owner", "unassigned policy", "ownership gap"],
        "priority": "P2",
        "suggested_owner_role": "Manager",
        "expected_risk_reduction": "Medium",
        "implementation_effort": "Low",
        "mitigations": [
            "Assign accountable owner",
            "Define review cycle",
            "Create approval workflow"
        ]
    },
    {
        "name": "Operational Tracking Gap",
        "keywords": ["operational tracking", "tracking control", "monitoring gap", "reporting cadence", "metric tracking"],
        "priority": "P3",
        "suggested_owner_role": "Analyst",
        "expected_risk_reduction": "Medium",
        "implementation_effort": "Medium",
        "mitigations": [
            "Improve tracking controls",
            "Define ownership",
            "Increase reporting cadence"
        ]
    }
]

def calculate_risk_score(severity: str, confidence: float, relevance: str = "medium", is_escalation: bool = False) -> int:
    """
    Computes a numeric risk score from 0 to 100 based on severity, confidence,
    governance relevance, and escalation status.
    """
    base_map = {
        "critical": 90,
        "high": 75,
        "medium": 50,
        "low": 25
    }
    base = base_map.get(severity.lower(), 50)
    
    relevance_map = {
        "high": 1.1,
        "medium": 1.0,
        "low": 0.8
    }
    relevance_mult = relevance_map.get(relevance.lower(), 1.0)
    
    escalation_premium = 10 if is_escalation else 0
    
    raw_score = (base * relevance_mult * confidence) + escalation_premium
    return min(100, max(0, int(round(raw_score))))

def get_default_mitigations(item_type: str) -> List[str]:
    """Provides fallback mitigations programmatically based on RAID item type."""
    t = item_type.lower()
    if t == "risk":
        return [
            "Conduct formal risk assessment",
            "Identify key risk indicators",
            "Establish mitigation controls"
        ]
    elif t == "issue":
        return [
            "Define root cause analysis",
            "Implement corrective action plan",
            "Track resolution progress"
        ]
    elif t == "action":
        return [
            "Assign action owner",
            "Set target due date",
            "Verify action completion"
        ]
    elif t == "dependency":
        return [
            "Establish dependency milestone",
            "Monitor critical path impact",
            "Coordinate cross-team alignment"
        ]
    else:
        return [
            "Define action plan",
            "Monitor progress",
            "Escalate if unresolved"
        ]

def get_default_remediation_plan(severity: str) -> str:
    """Provides a programmatic default remediation plan based on escalation severity."""
    sev = severity.lower()
    if sev in {"critical", "high"}:
        return "Review escalation evidence immediately, establish corrective action plan, assign critical resolution owner, and schedule daily stand-ups."
    return "Review escalation evidence, establish corrective action plan, assign remediation owner, and monitor on weekly cadence."

class PlaybookEngine:
    @staticmethod
    def match_playbook(text: str) -> Optional[Dict[str, Any]]:
        """Matches text against playbook keywords and returns the first matching playbook if found."""
        if not text:
            return None
            
        text_lower = text.lower()
        for playbook in PLAYBOOKS:
            matched = []
            for kw in playbook["keywords"]:
                # Use regex with word/boundary patterns or simple substring check
                # Simple boundary checks for flexible matching
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text_lower) or kw in text_lower:
                    matched.append(kw)
            if matched:
                return {
                    "playbook": playbook,
                    "matched_keywords": matched
                }
        return None

    @classmethod
    def enrich_raid_item(cls, item: Dict[str, Any], relevance: str = "medium") -> Dict[str, Any]:
        """
        Enriches a RAID item dict with decision support fields:
        mitigations, owner, effort, reduction, priority, score, and structured trace.
        """
        desc = item.get("description", "")
        match_result = cls.match_playbook(desc)
        
        # 1. Deterministic Playbook Match
        if match_result:
            playbook = match_result["playbook"]
            matched_kws = match_result["matched_keywords"]
            
            mitigations = playbook["mitigations"]
            owner = playbook["suggested_owner_role"]
            priority = playbook["priority"]
            effort = playbook["implementation_effort"]
            reduction = playbook["expected_risk_reduction"]
            source = "playbook"
            playbook_name = playbook["name"]
        else:
            # 2. Fallback Heuristics
            mitigations = get_default_mitigations(item.get("type", "risk"))
            
            # Map owner based on severity
            sev = item.get("severity", "medium").lower()
            if sev in {"critical", "high"}:
                owner = "Manager"
                priority = "P2"
                effort = "Medium"
                reduction = "High"
            else:
                owner = "Analyst"
                priority = "P3" if sev == "medium" else "P4"
                effort = "Low"
                reduction = "Medium"
            
            matched_kws = []
            source = "fallback_heuristics"
            playbook_name = None
            
        # 3. Calculate Risk Score
        score = calculate_risk_score(
            severity=item.get("severity", "medium"),
            confidence=item.get("confidence_score", 1.0),
            relevance=relevance,
            is_escalation=False
        )
        
        # 4. Structured Explainability Trace
        trace = {
            "playbook": playbook_name,
            "matched_keywords": matched_kws,
            "evidence": [item.get("source_excerpt") or desc],
            "recommendation_source": source
        }
        
        # Update/Enrich items
        enriched = dict(item)
        enriched["recommended_mitigations"] = mitigations
        enriched["suggested_owner_role"] = owner
        enriched["priority"] = priority
        enriched["recommended_priority"] = priority  # sync for backward compatibility
        enriched["implementation_effort"] = effort
        enriched["expected_risk_reduction"] = reduction
        enriched["risk_score"] = score
        
        # Priority 1 additions
        enriched["explain_why"] = item.get("explain_why") or f"This {item.get('type', 'risk')} could affect overall compliance and project milestones if left unaddressed."
        enriched["suggested_actions"] = item.get("suggested_actions") or "\n".join([f"- {m}" for m in mitigations])
        enriched["estimated_impact"] = item.get("estimated_impact") or f"Expected to result in {reduction.lower()} risk exposure reduction."
        
        enriched["explainability_trace"] = json.dumps(trace)
        
        return enriched

    @classmethod
    def enrich_escalation_item(cls, item: Dict[str, Any], relevance: str = "medium") -> Dict[str, Any]:
        """
        Enriches an Escalation item dict with decision support fields:
        remediation plan, suggested owner, priority, reduction, score, and structured trace.
        """
        desc = item.get("description", "")
        match_result = cls.match_playbook(desc)
        
        # 1. Deterministic Playbook Match
        if match_result:
            playbook = match_result["playbook"]
            matched_kws = match_result["matched_keywords"]
            
            # Build remediation plan from playbook mitigations
            plan = f"Follow the '{playbook['name']}' remediation playbook: " + "; ".join(playbook["mitigations"])
            owner = playbook["suggested_owner_role"]
            priority = playbook["priority"]
            reduction = playbook["expected_risk_reduction"]
            source = "playbook"
            playbook_name = playbook["name"]
        else:
            # 2. Fallback Heuristics
            sev = item.get("severity", "medium").lower()
            plan = get_default_remediation_plan(sev)
            
            # Escalations are higher profile, default to Governance Lead or Manager
            if sev in {"critical", "high"}:
                owner = "Governance Lead"
                priority = "P1"
                reduction = "High"
            else:
                owner = "Manager"
                priority = "P2"
                reduction = "Medium"
                
            matched_kws = []
            source = "fallback_heuristics"
            playbook_name = None
            
        # 3. Calculate Risk Score (Escalation Status = True)
        score = calculate_risk_score(
            severity=item.get("severity", "medium"),
            confidence=item.get("confidence_score", 1.0),
            relevance=relevance,
            is_escalation=True
        )
        
        # 4. Structured Explainability Trace
        trace = {
            "playbook": playbook_name,
            "matched_keywords": matched_kws,
            "evidence": [item.get("source_excerpt") or desc],
            "recommendation_source": source
        }
        
        # Update/Enrich items
        enriched = dict(item)
        enriched["remediation_plan"] = plan
        enriched["suggested_owner_role"] = owner
        enriched["priority"] = priority
        enriched["expected_risk_reduction"] = reduction
        enriched["risk_score"] = score
        
        # Priority 1 additions
        enriched["explain_why"] = item.get("explain_why") or f"Active escalation indicators require senior stakeholder review and remediation plan execution."
        enriched["suggested_actions"] = item.get("suggested_actions") or plan
        enriched["estimated_impact"] = item.get("estimated_impact") or f"Expected to result in {reduction.lower()} risk exposure reduction."
        
        enriched["explainability_trace"] = json.dumps(trace)
        
        return enriched
