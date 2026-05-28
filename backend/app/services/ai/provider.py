from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def extract_governance_data(self, text: str, context: str = "") -> dict:
        """
        Parses document text (with optional retrieved context) and returns
        a validated dictionary matching the AIReportExtractionSchema.
        
        Args:
            text: The main clean text of the document.
            context: Additional context chunks retrieved via RAG.
            
        Returns:
            dict containing:
                "summary": str,
                "executive_summary": str,
                "raid_items": list of dicts,
                "escalation_items": list of dicts,
                "confidence_score": float,
                "tokens_used": int
        """
        pass
