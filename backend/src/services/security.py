from openai import AsyncOpenAI
from llm_guard.input_scanners import PromptInjection, BanTopics
from llm_guard.input_scanners.prompt_injection import MatchType, V2_MODEL
from typing import Dict, Any
import asyncio

from ..core.config import Settings

class SecurityService:
    """Real implementation of security service using OpenAI and LLM-Guard"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        V2_MODEL.tokenizer_kwargs["token"] = settings.HUGGINGFACE_TOKEN
        V2_MODEL.kwargs["token"] = settings.HUGGINGFACE_TOKEN
        self.prompt_injection_scanner = PromptInjection(
            threshold=settings.PROMPT_INJECTION_THRESHOLD,
            match_type=MatchType.SENTENCE,
            model=V2_MODEL
        )
        self.ban_topics_scanner = BanTopics(
            topics=["hate", "violence", "nsfw", "self-harm"],
            threshold=settings.BAN_TOPICS_THRESHOLD,
            model=V2_MODEL
        )

    def _get_injection_message(self, risk_score: float) -> str:
        """Get a user-friendly message for prompt injection detection"""
        if risk_score > 0.8:
            return "This appears to be a severe prompt injection attempt. Please rephrase your query."
        elif risk_score > 0.5:
            return "Your query contains patterns that could be interpreted as prompt injection. Please try rewording it."
        else:
            return "Your query contains some suspicious patterns. Please try making it more straightforward."

    def _get_moderation_message(self, flagged_categories: Dict[str, float], no_banned_topics: bool) -> str:
        """Get a user-friendly message for content moderation"""
        if not flagged_categories and no_banned_topics:
            return None
        
        categories = list(flagged_categories.keys())
        if len(categories) == 1:
            return f"Your message was flagged for {categories[0]}. Please revise and try again."
        elif len(categories) > 1:
            categories_str = ", ".join(categories[:-1]) + f" and {categories[-1]}"
            return f"Your message was flagged for {categories_str}. Please revise and try again."
        elif not no_banned_topics:
            return "Your message was flagged for banned topics. Please revise and try again."
        return None

    async def check_prompt_injection(self, text: str) -> Dict[str, Any]:
        """
        Check if the text contains prompt injection attempts using LLM-Guard
        Returns detailed results about the injection check
        """
        try:
            sanitized_text, is_valid, risk_score = self.prompt_injection_scanner.scan(text)
            return {
                "is_safe": is_valid,
                "risk_score": risk_score,
                "sanitized_text": sanitized_text,
                "message": None if is_valid else self._get_injection_message(risk_score),
                "error": None
            }
        except Exception as e:
            return {
                "is_safe": False,
                "risk_score": None,
                "sanitized_text": None,
                "message": "Unable to check for prompt injection. Please try again later.",
                "error": str(e)
            }

    async def moderate_content(self, text: str) -> Dict[str, Any]:
        """
        Check if the content is safe using OpenAI's moderation API
        Returns detailed results about content moderation
        """
        try:
            response = await self.openai_client.moderations.create(
                model="omni-moderation-latest",
                input=text
            )
            
            result = response.results[0]
            
            # Get categories that were flagged by the API
            flagged_categories = {
                category: score
                for category, score in result.category_scores.model_dump().items()
                if result.categories.model_dump().get(category, True)
            }

            _, no_banned_topics, _ = self.ban_topics_scanner.scan(text)
            
            return {
                "is_safe": (not result.flagged) and no_banned_topics,
                "flagged_categories": flagged_categories,
                "all_scores": result.category_scores.model_dump(),
                "message": self._get_moderation_message(flagged_categories, no_banned_topics),
                "error": None
            }
        except Exception as e:
            return {
                "is_safe": False,
                "flagged_categories": None,
                "all_scores": None,
                "message": "Unable to check content safety. Please try again later.",
                "error": str(e)
            }

    async def analyze_safety(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive safety analysis returning detailed results
        """
        # Run both checks concurrently for faster response
        injection_result, content_result = await asyncio.gather(
            self.check_prompt_injection(text),
            self.moderate_content(text)
        )
        
        # Combine messages if both checks failed
        messages = []
        if injection_result.get("message"):
            messages.append(injection_result["message"])
        if content_result.get("message"):
            messages.append(content_result["message"])

        return {
            "is_safe": injection_result["is_safe"] and content_result["is_safe"],
            "prompt_injection": injection_result,
            "content_moderation": content_result,
            "message": " ".join(messages) if messages else None
        } 