"""Shared governance ontology vocabulary and semantic extraction settings."""

EXPLICIT_RAID_SECTION_PATTERNS = [
    r"^\s*risks?\s*:?\s*$",
    r"^\s*(?:critical\s+)?issues?\s*:?\s*$",
    r"^\s*actions?\s*:?\s*$",
    r"^\s*action items?\s*:\s*$",
    r"^\s*dependencies?\s*:?\s*$",
    r"^\s*raid\s*:?\s*$",
    r"^\s*risk register\s*:?\s*$",
    r"^\s*issue log\s*:?\s*$",
]

GENERIC_BUSINESS_PATTERNS = [
    "hr policy",
    "employee handbook",
    "travel and expense policy",
    "travel policy",
    "newsletter",
    "brochure",
    "marketing strategy",
    "training guide",
    "code of conduct",
    "facilities policy",
    "holiday calendar",
    "social media policy",
    "procurement policy",
    "conflict of interest",
    "diversity",
    "inclusion policy",
]

ONTOLOGY_TYPES = [
    "Risk",
    "Issue",
    "Dependency",
    "Decision",
    "Recommendation",
    "Approval",
    "Escalation",
    "ActionItem",
    "Observation",
    "StatusUpdate",
    "Mitigation",
    "Resolution",
    "GovernanceReview",
    "AuditFinding",
    "ComplianceConcern",
]

RAID_ONTOLOGY_TYPES = {
    "Risk": "risk",
    "Issue": "issue",
    "Dependency": "dependency",
    "ActionItem": "action",
}

DOCUMENT_TYPE_ENTITY_CAPS = {
    "governance_report": 18,
    "escalation_memo": 8,
    "raid_register": 18,
    "project_status_report": 24,
    "noisy_ocr_document": 10,
    "edge_case_document": 12,
}

MEETING_ACTION_CAPS = {
    "meeting_minutes": 12,
    "governance_report": 10,
    "escalation_memo": 10,
    "project_status_report": 12,
    "raid_register": 6,
    "noisy_ocr_document": 6,
    "edge_case_document": 6,
}

SEMANTIC_SIMILARITY_THRESHOLD = 0.82

