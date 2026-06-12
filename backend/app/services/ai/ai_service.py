import logging
import time
from backend.app.config import settings
from backend.app.schemas import AIReportExtractionSchema
from backend.app.services.ai.anthropic_provider import AnthropicProvider
from backend.app.services.ai.mock_provider import MockProvider

logger = logging.getLogger("governance_copilot.ai.service")

class AIService:
    def __init__(self):
        # Resolve AI Provider based on setting and key availability
        if settings.AI_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            logger.info("Initializing AIService with Anthropic Claude provider.")
            self.provider = AnthropicProvider()
            self.provider_name = "anthropic"
        else:
            logger.info("Initializing AIService with High-Fidelity Mock provider.")
            self.provider = MockProvider()
            self.provider_name = "mock"

    async def analyze_governance_document(self, text: str, context: str = "") -> dict:
        """
        Orchestrates document analysis:
        1. Selects active provider
        2. Retrieves parsed structured extraction
        3. Validates against AIReportExtractionSchema
        4. Logs metrics and errors
        """
        start_time = time.time()
        logger.info(f"AI Service processing document text (length: {len(text)}) using provider: {self.provider_name}")
        
        try:
            # Query provider for structured dict
            raw_data = await self.provider.extract_governance_data(text, context)
            
            # Add metrics placeholders if missing
            if "confidence_score" not in raw_data:
                raw_data["confidence_score"] = 0.90
            if "tokens_used" not in raw_data:
                raw_data["tokens_used"] = 0
                
            # SCHEMA VALIDATION: Force validation through Pydantic
            validated_data = AIReportExtractionSchema(**raw_data)
            
            processing_time = time.time() - start_time
            logger.info(f"Document analysis completed in {processing_time:.2f} seconds. Validation passed.")
            
            # Return validated dictionary merged with metadata
            result = validated_data.model_dump()
            result["processing_time_seconds"] = round(processing_time, 2)
            result["provider_name"] = self.provider_name
            return result
            
        except Exception as e:
            logger.error(f"Error in document analysis or schema validation: {e}")
            # Raise exception so workflow engine can record job failure
            raise ValueError(f"AI Service failed to parse and validate output: {str(e)}")

    async def generate_text_completion(self, prompt: str, system_instruction: str = "") -> str:
        """Exposes general text completion from the active provider."""
        return await self.provider.generate_text_completion(prompt, system_instruction)

