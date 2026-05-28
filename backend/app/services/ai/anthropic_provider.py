import json
import logging
import re
from anthropic import AsyncAnthropic
from backend.app.config import settings
from backend.app.services.ai.provider import AIProvider
from backend.app.schemas import DOCUMENT_TYPES, ESCALATION_TERMS

logger = logging.getLogger("governance_copilot.ai.anthropic")

class AnthropicProvider(AIProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-haiku-20240307"  # Fast, cost-efficient model for structured extraction

    async def extract_governance_data(self, text: str, context: str = "") -> dict:
        logger.info("Extracting governance data using Anthropic Claude...")
        
        # Load prompt templates
        from backend.app.config import PROMPTS_DIR
        try:
            with open(PROMPTS_DIR / "governance_v1.txt", "r") as f:
                gov_prompt = f.read()
            with open(PROMPTS_DIR / "raid_v1.txt", "r") as f:
                raid_prompt = f.read()
            with open(PROMPTS_DIR / "escalation_v1.txt", "r") as f:
                esc_prompt = f.read()
        except Exception as e:
            logger.error(f"Error loading prompt files: {e}")
            # Fallback inline prompts if files are not readable
            gov_prompt = "Extract governance summary."
            raid_prompt = "Extract RAID items."
            esc_prompt = "Extract escalations."

        system_instruction = (
            "You are a strict JSON extraction system. You must analyze the text and output a JSON object ONLY.\n"
            "Do not include any pre-text, conversational introductions, or post-text comments. Output only valid, parseable JSON.\n\n"
            f"SUMMARY GUIDELINES:\n{gov_prompt}\n\n"
            f"RAID GUIDELINES:\n{raid_prompt}\n\n"
            f"ESCALATION GUIDELINES:\n{esc_prompt}\n\n"
            "GOVERNANCE-AWARE ANALYSIS INSTRUCTIONS:\n"
            "1. Document Classification: Classify the document type based on content (meeting_minutes, project_status_report, raid_register, governance_report, steering_committee_pack, executive_report, generic_business_document).\n"
            "2. Governance Relevance Scoring: Assess governance relevance based on indicators like 'RAID', 'Risk Register', 'Escalation', 'Mitigation', 'Severity', 'Owner', 'Target Date', 'RAG', 'Steering Committee'.\n"
            "3. Governance Guardrail: If fewer than 3 governance keywords exist and the text does not contain explicit RAID section headers, set governance_relevance to 'low' and skip RAID extraction.\n"
            "4. Explicit RAID Section Override: If the text contains section headers such as Risks:, Risk:, Issues:, Issue:, Actions:, Action Items:, Dependencies:, RAID:, Risk Register:, or Issue Log:, set document_type to 'governance_report', governance_relevance to 'high', classification_confidence to at least 0.90, and parse each listed bullet as a separate RAID item.\n"
            "5. Low Relevance Documents: If governance_relevance is 'low', return empty raid_items and escalation_items. Extract meeting_actions instead (owner, task, due_date).\n"
            "6. Strict Escalation Detection: Only create escalations when explicit escalation language exists: " + ", ".join(ESCALATION_TERMS) + ". Do NOT infer escalation from severity, risk, or delay alone.\n"
            "7. No Fabrication: NEVER fabricate fallback RAID items or escalations. Return empty lists when no governance content exists.\n\n"
            "Your output must follow this JSON schema exactly:\n"
            "{\n"
            "  \"summary\": \"A concise, structured governance summary of the project status.\",\n"
            "  \"executive_summary\": \"A high-level 2-3 sentence overview suitable for executive leaders.\",\n"
            "  \"raid_items\": [\n"
            "    {\n"
            "      \"type\": \"risk | action | issue | dependency\",\n"
            "      \"description\": \"Item description\",\n"
            "      \"severity\": \"low | medium | high | critical\",\n"
            "      \"confidence_score\": 0.9,\n"
            "      \"source_excerpt\": \"Verbatim sentence matching this item\"\n"
            "    }\n"
            "  ],\n"
            "  \"escalation_items\": [\n"
            "    {\n"
            "      \"description\": \"Actionable escalation summary\",\n"
            "      \"severity\": \"low | medium | high | critical\",\n"
            "      \"source_excerpt\": \"Verbatim sentence matching this escalation\",\n"
            "      \"confidence_score\": 0.85\n"
            "    }\n"
            "  ],\n"
            "  \"meeting_actions\": [\n"
            "    {\n"
            "      \"owner\": \"Person name\",\n"
            "      \"task\": \"Action description\",\n"
            "      \"due_date\": \"Optional due date\"\n"
            "    }\n"
            "  ],\n"
            "  \"document_type\": \"meeting_minutes | project_status_report | raid_register | governance_report | steering_committee_pack | executive_report | generic_business_document\",\n"
            "  \"classification_confidence\": 0.85,\n"
            "  \"governance_relevance\": \"low | medium | high\"\n"
            "}"
        )

        user_content = f"Source text to analyze:\n```\n{text}\n```"
        if context:
            user_content = f"Retrieved Context:\n```\n{context}\n```\n\n" + user_content

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.0,  # Low temperature for deterministic output
                system=system_instruction,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )
            
            response_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            logger.info(f"Claude API call finished. Tokens used: {tokens_used}")
            
            extracted_json = self._clean_and_parse_json(response_text)
            extracted_json["tokens_used"] = tokens_used
            return extracted_json
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise RuntimeError(f"Anthropic provider failed: {str(e)}")

    def _clean_and_parse_json(self, text: str) -> dict:
        """Cleans and extracts JSON content from model output."""
        text = text.strip()
        
        # Look for code block markdown tags
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Fallback to finding first { and last }
            first_brace = text.find("{")
            last_brace = text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                json_str = text[first_brace:last_brace + 1]
            else:
                json_str = text
                
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse JSON string: '{json_str[:200]}...' Error: {e}")
            raise ValueError(f"Invalid JSON returned by provider: {str(e)}")
