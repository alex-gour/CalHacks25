"""Google Custom Search API service for finding Shopify product URLs."""

import os
import aiohttp
from typing import List, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Represents a search result from Google."""
    title: str
    url: str
    snippet: str


class GoogleSearchService:
    """Service for searching Shopify products using Google Custom Search API."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

        if not self.api_key:
            raise ValueError("GOOGLE_SEARCH_API_KEY environment variable not set")
        if not self.search_engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID environment variable not set")

        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search_shopify_product(
        self,
        product_label: str,
        max_results: int = 5
    ) -> List[SearchResult]:
        """
        Search for a Shopify product URL based on the product label.

        Args:
            product_label: Product description from Gemini (e.g., "shampoo bottle, white, pump")
            max_results: Maximum number of results to return

        Returns:
            List of search results containing Shopify URLs
        """
        # Construct search query to specifically find product pages, not collections
        # Use inurl:products to ensure we get actual product pages
        query = f"{product_label} inurl:products buy"

        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(max_results, 10)  # API max is 10
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Google Search API error: {response.status} - {error_text}")

                    data = await response.json()

                    results = []
                    if "items" in data:
                        for item in data["items"]:
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("link", ""),
                                snippet=item.get("snippet", "")
                            ))

                    return results

        except Exception as e:
            print(f"Error searching for product: {e}")
            raise

    async def find_best_shopify_url(self, product_label: str) -> Optional[str]:
        """
        Find the best matching Shopify URL for a product.

        Args:
            product_label: Product description from Gemini

        Returns:
            The best matching Shopify URL, or None if not found
        """
        results = await self.search_shopify_product(product_label, max_results=10)

        # Prioritize results with /products/ in the URL (actual product pages)
        # Exclude /collections/ URLs
        product_page_results = [
            r for r in results
            if "/products/" in r.url and "/collections/" not in r.url
        ]

        if product_page_results:
            # Return the first product page result
            return product_page_results[0].url

        # Fall back to any Shopify URL with /products/
        shopify_product_results = [
            r for r in results
            if "/products/" in r.url
        ]

        if shopify_product_results:
            return shopify_product_results[0].url

        # Last resort: any result that's not a collection page
        non_collection_results = [
            r for r in results
            if "/collections/" not in r.url
        ]

        if non_collection_results:
            return non_collection_results[0].url

        # If all else fails, return the first result
        if results:
            return results[0].url

        return None


# Singleton instance
_search_service: Optional[GoogleSearchService] = None


def get_search_service() -> GoogleSearchService:
    """Get or create the Google search service singleton."""
    global _search_service
    if _search_service is None:
        _search_service = GoogleSearchService()
    return _search_service
