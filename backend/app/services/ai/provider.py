from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def extract_governance_data(self, text: str, context: str = "") -> dict:
        """
        Parses document text (with optional retrieved context) and returns
        a validated dictionary matching the AIReportExtractionSchema.
        """
        pass

    @abstractmethod
    async def generate_text_completion(self, prompt: str, system_instruction: str = "") -> str:
        """
        Generates a general text completion response from the AI provider.
        """
        pass

