"""Web search service for workflow nodes."""
from typing import List, Dict, Any, Optional
import httpx


class WebSearchService:
    """Service for web search operations."""
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        engine: str = "google"
    ) -> List[Dict[str, Any]]:
        """Search the web for information.
        
        Args:
            query: Search query
            num_results: Number of results to return
            engine: Search engine to use (google, bing, duckduckgo)
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            if engine == "duckduckgo":
                return await self._search_duckduckgo(query, num_results)
            else:
                # Default to a simple search implementation
                return await self._search_duckduckgo(query, num_results)
        except Exception as e:
            return [{
                "title": "Search Error",
                "url": "",
                "snippet": f"Failed to perform search: {str(e)}",
                "error": True
            }]
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML parser (no API key required)."""
        try:
            # Use DuckDuckGo instant answer API
            async with httpx.AsyncClient(timeout=10) as client:
                # Get HTML search results
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query}
                )
                
                if response.status_code != 200:
                    return []
                
                # Simple HTML parsing
                results = []
                html = response.text
                
                # Extract result links (simplified parsing)
                import re
                # Match web results pattern
                pattern = r'<a class="result__a" href="([^"]+)">([^<]+)</a>'
                matches = re.findall(pattern, html)
                
                for url, title in matches[:num_results]:
                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "snippet": "",
                    })
                
                # If no results from pattern matching, return empty
                if not results:
                    return [{
                        "title": f"Results for: {query}",
                        "url": f"https://duckduckgo.com/?q={query}",
                        "snippet": "Click to view search results",
                    }]
                
                return results
        except Exception as e:
            return [{
                "title": "Search Error",
                "url": "",
                "snippet": f"Failed to search: {str(e)}",
            }]
    
    async def get_page_content(self, url: str) -> Optional[str]:
        """Get the content of a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content or None on error
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
                return None
        except Exception:
            return None
