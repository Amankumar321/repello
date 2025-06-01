import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import trafilatura

from ..models.schema import SearchResult
from ..core.config import Settings
from ..services.security import SecurityService

class SearchService:
    """Implementation of search service using Google Custom Search API"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.endpoint = "https://www.googleapis.com/customsearch/v1"
        self.headers = {
            "Accept": "application/json"
        }
        self.security_service = SecurityService(settings)
        
    async def search(self, query: str, num_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform a web search using Google Custom Search API
        """
        if num_results is None:
            num_results = self.settings.DEFAULT_SEARCH_RESULTS
            
        num_results = min(num_results, self.settings.MAX_SEARCH_RESULTS)
        
        params = {
            "q": query,
            "key": self.settings.GOOGLE_API_KEY,
            "cx": self.settings.GOOGLE_SEARCH_ENGINE_ID,
            "num": num_results
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.endpoint,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "items" not in data:
                    return []
                
                search_results = []
                for item in data["items"]:
                    # Extract content from URL
                    content = await self.extract_content(item.get("link", "")) or item.get("snippet", "")
                    
                    if content:
                        # Check content safety
                        safety_result = await self.security_service.analyze_safety(content)
                        if not safety_result["is_safe"]:
                            # Skip this result if it's not safe
                            continue
                        
                    search_results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=content or item.get("snippet", ""),
                            source=self._extract_domain(item.get("link", "")),
                            timestamp=datetime.now(),
                            relevance_score=self._calculate_relevance(item, query)
                        )
                    )
                
                return search_results
                
            except Exception as e:
                # Log the error here
                raise Exception(f"Search failed: {str(e)}")
    
    async def extract_content(self, url: str) -> Optional[str]:
        """
        Extract and sanitize content from a URL using trafilatura
        """
        if not url:
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                # Use trafilatura for better content extraction
                content = trafilatura.extract(
                    response.text,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=True
                )
                
                if content:
                    # Limit content length but try to keep complete sentences
                    return self._truncate_to_sentences(content, 2000)
                    
                return None
                
            except Exception:
                return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            return urlparse(url).netloc
        except:
            return url
            
    def _calculate_relevance(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score based on multiple factors"""
        # Start with base score
        score = 1.0
        
        # Boost score based on title match
        if query.lower() in result.get("title", "").lower():
            score += 0.3
            
        # Consider page rank if available
        if "pagerank" in result:
            score += float(result["pagerank"]) * 0.2
            
        return min(score, 1.0)
        
    def _truncate_to_sentences(self, text: str, max_length: int) -> str:
        """Truncate text to max_length while preserving complete sentences"""
        if len(text) <= max_length:
            return text
            
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > 0:
            return truncated[:last_period + 1]
        
        return truncated 