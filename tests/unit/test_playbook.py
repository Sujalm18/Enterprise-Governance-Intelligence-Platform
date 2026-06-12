import json
import pytest
from backend.app.services.governance.playbook import (
    calculate_risk_score,
    PlaybookEngine,
    PLAYBOOKS
)

def test_calculate_risk_score():
    # Base check for critical severity (base=90), relevance=medium (mult=1.0), conf=1.0, is_esc=False -> 90
    assert calculate_risk_score("critical", 1.0, "medium", False) == 90
    
    # Base check with relevance=high (mult=1.1) -> 90 * 1.1 = 99
    assert calculate_risk_score("critical", 1.0, "high", False) == 99
    
    # Check escalation premium (+10) -> (90 * 1.1 * 1.0) + 10 = 109 capped at 100
    assert calculate_risk_score("critical", 1.0, "high", True) == 100
    
    # Check low severity (base=25), relevance=low (mult=0.8), confidence=0.8, is_esc=True
    # (25 * 0.8 * 0.8) + 10 = 16 + 10 = 26
    assert calculate_risk_score("low", 0.8, "low", True) == 26

def test_playbook_matching():
    # Match vendor dependency
    res = PlaybookEngine.match_playbook("We identified a vendor dependency issue with a supplier.")
    assert res is not None
    assert res["playbook"]["name"] == "Vendor Dependency"
    assert "vendor" in res["matched_keywords"]
    assert "supplier" in res["matched_keywords"]

    # Match AI governance
    res2 = PlaybookEngine.match_playbook("The prompt injections in our LLM genai model show high bias.")
    assert res2 is not None
    assert res2["playbook"]["name"] == "AI Governance Risk"
    assert "llm" in res2["matched_keywords"]

    # Match security control gap
    res3 = PlaybookEngine.match_playbook("Unauthorized access control vulnerability in authorization mechanism.")
    assert res3 is not None
    assert res3["playbook"]["name"] == "Security Control Gap"
    assert "access control" in res3["matched_keywords"]

    # Unmatched text
    res_none = PlaybookEngine.match_playbook("This is a random sentence that should not match anything.")
    assert res_none is None

def test_enrich_raid_item():
    item = {
        "type": "risk",
        "description": "We are facing a supplier capacity vendor dependency.",
        "severity": "high",
        "confidence_score": 0.9,
        "source_excerpt": "supplier capacity vendor dependency"
    }
    
    enriched = PlaybookEngine.enrich_raid_item(item, relevance="high")
    
    assert enriched["suggested_owner_role"] == "Manager"
    assert enriched["priority"] == "P1"
    assert enriched["expected_risk_reduction"] == "High"
    assert len(enriched["recommended_mitigations"]) == 3
    assert enriched["risk_score"] > 0
    
    trace = json.loads(enriched["explainability_trace"])
    assert trace["playbook"] == "Vendor Dependency"
    assert trace["recommendation_source"] == "playbook"

def test_enrich_raid_item_fallback():
    item = {
        "type": "risk",
        "description": "A minor operational problem that does not match any playbook.",
        "severity": "low",
        "confidence_score": 1.0,
        "source_excerpt": "minor operational problem"
    }
    
    enriched = PlaybookEngine.enrich_raid_item(item, relevance="medium")
    
    assert enriched["suggested_owner_role"] == "Analyst"
    assert enriched["priority"] == "P4"
    assert enriched["implementation_effort"] == "Low"
    assert enriched["expected_risk_reduction"] == "Medium"
    
    trace = json.loads(enriched["explainability_trace"])
    assert trace["playbook"] is None
    assert trace["recommendation_source"] == "fallback_heuristics"
