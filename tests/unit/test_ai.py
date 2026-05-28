import pytest
from backend.app.schemas import AIReportExtractionSchema
from backend.app.services.ai.mock_provider import MockProvider
from backend.app.services.ai.ai_service import AIService

@pytest.mark.asyncio
async def test_mock_provider_heuristics():
    provider = MockProvider()
    text = (
        "Project Orion status report. We have a severe delay in database migrations. "
        "This is an active blocker for front-end teams. Action: PM to align migration schedule "
        "by next Friday. Risk: potential API availability delays. Escalation: Vendor billing "
        "dispute requires executive attention."
    )
    
    extracted_data = await provider.extract_governance_data(text)
    
    assert "summary" in extracted_data
    assert "executive_summary" in extracted_data
    assert len(extracted_data["raid_items"]) > 0
    assert len(extracted_data["escalation_items"]) > 0
    
    # Assert that actual source excerpts match phrases in original text
    raid_types = [item["type"] for item in extracted_data["raid_items"]]
    assert "risk" in raid_types or "issue" in raid_types

@pytest.mark.asyncio
async def test_ai_service_orchestration_and_validation():
    # Force Mock Mode config to test validation
    service = AIService()
    text = "Status: Project Apollo is progressing on schedule. No critical issues reported."
    
    result = await service.analyze_governance_document(text)
    
    # Validate result fields injected by AI Service
    assert "processing_time_seconds" in result
    assert result["provider_name"] == "mock"
    
    # Schema check
    validated = AIReportExtractionSchema(**result)
    assert validated.confidence_score >= 0.0 and validated.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_mock_provider_structured_raid_extraction():
    provider = MockProvider()
    text = (
        "Project Orion status report.\n"
        "Risks:\n"
        "- API integration delays\n"
        "- Limited testing resources\n\n"
        "Actions:\n"
        "- Complete integration testing\n"
        "- Assign QA owner\n\n"
        "Issues:\n"
        "- Authentication service unstable\n\n"
        "Dependencies:\n"
        "- Azure OpenAI access approval\n"
    )

    extracted = await provider.extract_governance_data(text)
    raid = extracted.get("raid_items", [])

    # Expect at least one of each type
    assert any(i["type"] == "risk" for i in raid)
    assert any(i["type"] == "action" for i in raid)
    assert any(i["type"] == "issue" for i in raid)
    assert any(i["type"] == "dependency" for i in raid)

    # Ensure source excerpts correspond to bullets and are not duplicated across categories
    excerpts = [item.get("source_excerpt") for item in raid if item.get("source_excerpt")]
    joined = " ".join(excerpts)
    assert "API integration delays" in joined
    assert "Limited testing resources" in joined
    assert len(excerpts) == len(set(excerpts))


@pytest.mark.asyncio
async def test_project_status_report_generates_raid_items():
    provider = MockProvider()
    text = (
        "Project: AI Governance Platform\n\n"
        "Risks:\n"
        "- API integration delays\n\n"
        "Actions:\n"
        "- Complete integration testing\n\n"
        "Issues:\n"
        "- Authentication service unstable\n\n"
        "Dependencies:\n"
        "- Azure OpenAI access approval\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["raid_items"]) == 4
    assert result["governance_relevance"] == "high"
    assert result["document_type"] == "governance_report"


@pytest.mark.asyncio
async def test_meeting_minutes_without_raid_sections_produces_no_raid_items():
    provider = MockProvider()
    text = (
        "Meeting Minutes\n\n"
        "Attendees:\n"
        "- John\n"
        "- Jane\n\n"
        "Agenda:\n"
        "- Weekly sync\n\n"
        "Discussion:\n"
        "- Reviewed delivery progress\n\n"
        "Notes:\n"
        "- Keep monitoring testing schedule\n\n"
        "Next Meeting:\n"
        "- Friday\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["raid_items"]) == 0
    assert result["governance_relevance"] in ["low", "medium"]


@pytest.mark.asyncio
async def test_explicit_raid_sections_override_keyword_guardrail():
    provider = MockProvider()
    text = (
        "Risks:\n"
        "- API delay\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["raid_items"]) == 1
    assert result["raid_items"][0]["type"] == "risk"
    assert result["raid_items"][0]["description"] == "API delay"
    assert result["governance_relevance"] == "high"
    assert result["document_type"] == "governance_report"


@pytest.mark.asyncio
async def test_meeting_minutes_no_raid_items():
    """Test that meeting minutes produce no RAID items and governance_relevance is low."""
    provider = MockProvider()
    text = (
        "Meeting Minutes\n"
        "Attendees: John, Jane, Mike\n"
        "Agenda: Project status update\n"
        "Discussion: Testing progress reviewed\n"
        "John to update timeline.\n"
        "Jane to circulate report.\n"
        "Outstanding issues discussed."
    )
    
    extracted = await provider.extract_governance_data(text)
    
    # Should have empty RAID items
    assert len(extracted["raid_items"]) == 0
    assert len(extracted["escalation_items"]) == 0
    
    # Should have meeting actions
    assert len(extracted["meeting_actions"]) > 0
    
    # Should have low governance relevance
    assert extracted["governance_relevance"] == "low"
    
    # Should be classified as meeting minutes
    assert extracted["document_type"] == "meeting_minutes"


@pytest.mark.asyncio
async def test_meeting_actions_extraction():
    """Test that meeting actions are extracted correctly."""
    provider = MockProvider()
    text = (
        "Meeting Notes\n"
        "John to send updated report by Friday.\n"
        "Jane to review budget.\n"
        "Mike to circulate meeting notes."
    )
    
    extracted = await provider.extract_governance_data(text)
    
    # Should extract meeting actions
    assert len(extracted["meeting_actions"]) >= 2
    
    # Check action structure
    actions = extracted["meeting_actions"]
    owners = [action["owner"] for action in actions]
    assert "John" in owners or "Jane" in owners or "Mike" in owners
    
    # Each action should have owner and task
    for action in actions:
        assert "owner" in action
        assert "task" in action
        assert len(action["task"]) > 0


@pytest.mark.asyncio
async def test_meeting_minutes_extract_actions():
    provider = MockProvider()
    text = (
        "Meeting Minutes\n"
        "Attendees: John, Jane, Infrastructure Team\n"
        "Discussion: Delivery actions reviewed.\n"
        "John to circulate updated report by Friday\n"
        "Jane to update project timeline\n"
        "Assigned To: Infrastructure Team\n"
        "Action Item: Provision test access by Monday\n"
        "Follow Up: Confirm QA owner\n"
        "Next Step: Schedule readiness review\n"
        "Responsible: PMO Team\n"
        "Due Date: Friday\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["meeting_actions"]) >= 5
    assert any(action["owner"] == "John" and "circulate updated report" in action["task"] for action in result["meeting_actions"])
    assert any(action["owner"] == "Jane" and "update project timeline" in action["task"] for action in result["meeting_actions"])
    assert len(result["raid_items"]) == 0


@pytest.mark.asyncio
async def test_meeting_minutes_no_false_escalations():
    provider = MockProvider()
    text = (
        "Meeting Minutes\n"
        "Vendor management team to conduct escalation meeting\n"
        "Steering committee approved additional testing resources\n"
        "Escalation to CIO approved if delay exceeds 14 days\n"
        "Jane to update project timeline\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["escalation_items"]) == 0
    assert len(result["meeting_actions"]) >= 1


@pytest.mark.asyncio
async def test_project_status_report_extracts_risks():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Risks:\n"
        "1. Vendor may miss API deadline\n"
    )

    result = await provider.extract_governance_data(text)

    assert any(item["type"] == "risk" and "Vendor may miss API deadline" in item["description"] for item in result["raid_items"])


@pytest.mark.asyncio
async def test_project_status_report_extracts_issues():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Issues:\n"
        "1. Test environment unstable\n"
    )

    result = await provider.extract_governance_data(text)

    assert any(item["type"] == "issue" and "Test environment unstable" in item["description"] for item in result["raid_items"])


@pytest.mark.asyncio
async def test_project_status_report_extracts_actions():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Actions:\n"
        "1. Provision servers by Friday\n"
    )

    result = await provider.extract_governance_data(text)

    assert any(item["type"] == "action" and "Provision servers by Friday" in item["description"] for item in result["raid_items"])


@pytest.mark.asyncio
async def test_decisions_not_escalations():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Steering committee approved additional testing resources\n"
        "Risks:\n"
        "- API integration delay\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["escalation_items"]) == 0


@pytest.mark.asyncio
async def test_escalation_meeting_not_escalation():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Vendor management team to conduct escalation meeting\n"
        "Risks:\n"
        "- Vendor response delay\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["escalation_items"]) == 0


@pytest.mark.asyncio
async def test_real_escalation_detected():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Risks:\n"
        "- API deadline at risk\n"
        "Escalated to CIO for decision on vendor funding.\n"
        "Executive intervention requested for authentication outage.\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["escalation_items"]) == 2


@pytest.mark.asyncio
async def test_summary_matches_extracted_counts():
    provider = MockProvider()
    text = (
        "Project Status Report\n"
        "Risks:\n"
        "- API integration delays\n"
        "- Limited testing resources\n"
        "Actions:\n"
        "- Complete integration testing\n"
        "- Assign QA owner\n"
        "Issues:\n"
        "- Authentication service unstable\n"
        "Dependencies:\n"
        "- Azure OpenAI access approval\n"
        "John to circulate updated report by Friday\n"
        "Jane to update project timeline\n"
        "Escalation raised for authentication outage.\n"
    )

    result = await provider.extract_governance_data(text)

    assert len(result["raid_items"]) == 6
    assert len(result["meeting_actions"]) >= 2
    assert len(result["escalation_items"]) == 1
    assert "6 RAID items" in result["summary"]
    assert f"{len(result['meeting_actions'])} meeting actions" in result["summary"]
    assert "1 escalations" in result["summary"]
    assert "0 RAID items" not in result["summary"]


@pytest.mark.asyncio
async def test_generic_document_empty_raid():
    """Test that generic business documents produce empty RAID output."""
    provider = MockProvider()
    text = (
        "Business Proposal\n"
        "This document outlines our proposal for the new service offering.\n"
        "We aim to provide excellent customer service.\n"
        "Contact us for more information."
    )
    
    extracted = await provider.extract_governance_data(text)
    
    # Should have empty RAID items
    assert len(extracted["raid_items"]) == 0
    assert len(extracted["escalation_items"]) == 0
    
    # Should have low governance relevance
    assert extracted["governance_relevance"] == "low"
    
    # Should be classified as generic business document
    assert extracted["document_type"] == "generic_business_document"


@pytest.mark.asyncio
async def test_policy_obligations_do_not_become_meeting_actions():
    provider = MockProvider()
    text = (
        "HR Policy\n"
        "Managers must review requests before submission.\n"
        "Employees are required to comply with the travel policy.\n"
        "HR will maintain records for audit purposes.\n"
        "Approvals require director signoff.\n"
    )

    extracted = await provider.extract_governance_data(text)

    assert extracted["governance_relevance"] == "low"
    assert extracted["raid_items"] == []
    assert extracted["escalation_items"] == []
    assert extracted["meeting_actions"] == []


@pytest.mark.asyncio
async def test_source_file_metadata_not_used_in_summaries():
    provider = MockProvider()
    text = (
        "SOURCE_FILE: 1779951094_escalation_memo_05.txt\n"
        "Escalation Memo\n"
        "Project: Identity Platform Recovery\n"
        "Formal escalation initiated for authentication outage.\n"
    )

    extracted = await provider.extract_governance_data(text)

    assert "SOURCE_FILE" not in extracted["summary"]
    assert "1779951094" not in extracted["summary"]
    assert "escalation_memo_05" not in extracted["executive_summary"]
    assert "Identity Platform Recovery" in extracted["summary"]


@pytest.mark.asyncio
async def test_escalation_memo_rejects_fragments_and_headings():
    provider = MockProvider()
    text = (
        "Escalation Memo\n"
        "IMPACT ASSESSMENT\n"
        "----------------\n"
        "1. blocking\n"
        "2. Vendor integration failure is delaying authentication rollout\n"
        "3. Test environment instability is blocking release validation\n"
        "Formal escalation initiated for executive intervention.\n"
    )

    extracted = await provider.extract_governance_data(text)
    descriptions = [item["description"] for item in extracted["raid_items"]]

    assert len(descriptions) <= 3
    assert "blocking" not in descriptions
    assert "IMPACT ASSESSMENT" not in descriptions
    assert all("-" not in description for description in descriptions)
    assert len(extracted["escalation_items"]) == 1


@pytest.mark.asyncio
async def test_structured_register_reconstructs_one_object_per_row():
    provider = MockProvider()
    text = (
        "SHEET: RAID Register\n"
        "HEADERS: ID | Type | Description | Owner | Due Date | Status | Severity | Mitigation\n"
        "ROW: ID: R1 | Type: risk | Description: Vendor integration delay threatens release | "
        "Owner: PMO | Due Date: Friday | Status: Open | Severity: High | Mitigation: Executive vendor review\n"
        "ROW: ID: R2 | Type: risk | Description: Vendor integration delay threatens release timeline | "
        "Owner: PMO | Due Date: Monday | Status: Open | Severity: High | Mitigation: Daily tracking\n"
    )

    extracted = await provider.extract_governance_data(text)

    assert len(extracted["raid_items"]) == 1
    assert extracted["raid_items"][0]["type"] == "risk"
    assert "Vendor integration delay" in extracted["raid_items"][0]["description"]


@pytest.mark.asyncio
async def test_decisions_and_approvals_do_not_become_raid_items():
    provider = MockProvider()
    text = (
        "Steering Committee Report\n"
        "DECISIONS\n"
        "Decision 1: Approved go-live date for July 15\n"
        "APPROVALS\n"
        "Approval 1: Approved performance testing budget\n"
        "RISKS\n"
        "- Vendor integration delay threatens release\n"
    )

    extracted = await provider.extract_governance_data(text)

    descriptions = " ".join(item["description"] for item in extracted["raid_items"])
    assert len(extracted["raid_items"]) == 1
    assert "Vendor integration delay" in descriptions
    assert "Approved go-live" not in descriptions
    assert "performance testing budget" not in descriptions


@pytest.mark.asyncio
async def test_governance_commentary_does_not_inflate_actions():
    provider = MockProvider()
    text = (
        "Meeting Minutes\n"
        "Discussion: Committee discussed migration readiness.\n"
        "Observation: Monitoring should continue.\n"
        "Recommendation: Vendor engagement required.\n"
        "Action Items\n"
        "1. PMO to submit revised timeline by Friday\n"
        "2. Vendor to provide RCA by Monday\n"
    )

    extracted = await provider.extract_governance_data(text)

    assert len(extracted["meeting_actions"]) == 2
    tasks = " ".join(action["task"] for action in extracted["meeting_actions"])
    assert "discussed migration readiness" not in tasks
    assert "Monitoring should continue" not in tasks


@pytest.mark.asyncio
async def test_raid_register_extraction():
    """Test that RAID registers produce RAID items with high governance relevance."""
    provider = MockProvider()
    text = (
        "Risk Register\n"
        "Project: Enterprise CRM Modernization\n"
        "Risks:\n"
        "- Vendor integration delay\n"
        "- API availability issues\n\n"
        "Mitigation:\n"
        "Weekly escalation review\n\n"
        "Owner:\n"
        "Program Manager"
    )
    
    extracted = await provider.extract_governance_data(text)
    
    # Should have RAID items
    assert len(extracted["raid_items"]) > 0
    
    # Should have high governance relevance
    assert extracted["governance_relevance"] == "high"
    
    assert extracted["document_type"] == "raid_register"
    
    # Check RAID item types
    raid_types = [item["type"] for item in extracted["raid_items"]]
    assert "risk" in raid_types


@pytest.mark.asyncio
async def test_strict_escalation_detection():
    """Test that escalations only appear with explicit escalation language."""
    provider = MockProvider()
    
    # Text with explicit escalation language
    text_with_escalation = (
        "Project Status Report\n"
        "Risk: API integration delay\n"
        "Escalation: This issue requires steering committee intervention.\n"
        "Issue: Database migration blocked"
    )
    
    extracted_with = await provider.extract_governance_data(text_with_escalation)
    
    # Should have escalation due to explicit language
    assert len(extracted_with["escalation_items"]) > 0
    
    # Text without explicit escalation language
    text_without_escalation = (
        "Project Status Report\n"
        "Risk: API integration delay\n"
        "Issue: Database migration blocked\n"
        "Action: Complete migration by Friday"
    )
    
    extracted_without = await provider.extract_governance_data(text_without_escalation)
    
    # Should NOT have escalation without explicit language
    assert len(extracted_without["escalation_items"]) == 0


@pytest.mark.asyncio
async def test_no_fabricated_fallback_items():
    """Test that no fabricated fallback items are generated."""
    provider = MockProvider()
    text = (
        "Simple Document\n"
        "This is a simple document with no governance content.\n"
        "It contains basic information only."
    )
    
    extracted = await provider.extract_governance_data(text)
    
    # Should have empty lists, no fabricated items
    assert len(extracted["raid_items"]) == 0
    assert len(extracted["escalation_items"]) == 0
    
    # Should have low governance relevance
    assert extracted["governance_relevance"] == "low"


@pytest.mark.asyncio
async def test_governance_relevance_scoring():
    """Test that governance relevance scoring behaves correctly."""
    provider = MockProvider()
    
    # High relevance text
    high_relevance_text = (
        "Risk Register\n"
        "RAID items tracking\n"
        "Escalation process\n"
        "Mitigation strategies\n"
        "Severity assessment\n"
        "Owner assignment\n"
        "Target date tracking\n"
        "RAG status\n"
        "Steering committee review"
    )
    
    extracted_high = await provider.extract_governance_data(high_relevance_text)
    assert extracted_high["governance_relevance"] == "high"
    
    # Low relevance text
    low_relevance_text = (
        "Meeting Minutes\n"
        "Agenda items\n"
        "Discussion points\n"
        "Action items\n"
        "Attendees list"
    )
    
    extracted_low = await provider.extract_governance_data(low_relevance_text)
    assert extracted_low["governance_relevance"] == "low"


@pytest.mark.asyncio
async def test_improved_project_name_detection():
    """Test that project name detection uses stricter patterns."""
    provider = MockProvider()
    
    # Valid project name pattern
    valid_text = (
        "Project: Enterprise CRM Modernization\n"
        "Risk: API integration delay"
    )
    
    extracted_valid = await provider.extract_governance_data(valid_text)
    # Should extract the project name correctly
    assert "Enterprise CRM Modernization" in extracted_valid["summary"] or "CRM" in extracted_valid["summary"]
    
    # Invalid pattern (should not extract "Project Manager" as project name)
    invalid_text = (
        "Project Manager: John Smith\n"
        "Meeting notes for today"
    )
    
    extracted_invalid = await provider.extract_governance_data(invalid_text)
    # Should not incorrectly identify "Project Manager" as project name
    assert "Project Manager" not in extracted_invalid["summary"] or "John Smith" not in extracted_invalid["summary"]


@pytest.mark.asyncio
async def test_governance_guardrail_keyword_count():
    """Test that governance guardrail works with keyword count."""
    provider = MockProvider()
    
    # Text with fewer than 3 governance keywords
    low_keyword_text = (
        "Meeting Notes\n"
        "Discussion about project progress\n"
        "Action items assigned"
    )
    
    extracted_low = await provider.extract_governance_data(low_keyword_text)
    assert extracted_low["governance_relevance"] == "low"
    assert len(extracted_low["raid_items"]) == 0
