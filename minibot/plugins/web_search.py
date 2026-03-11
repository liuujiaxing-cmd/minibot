from ..tools import tool
from duckduckgo_search import DDGS

# --- SKILL METADATA ---
# Description: Search the internet for real-time information.
# Input: query (string)
# Output: Markdown list of search results.
# Constraints: Max 5 results. Do not hallucinate URLs.

@tool(name="web_search", description="Search the web using DuckDuckGo. Usage: web_search(query='latest AI news')")
def web_search(query: str):
    """Perform a web search."""
    try:
        # Note: DDGS().text() returns a generator in newer versions or a list in older ones.
        # It's safer to wrap in list() if it's an iterator.
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return "No results found."
        
        formatted_results = ""
        for r in results:
            formatted_results += f"- {r.get('title', 'No Title')}: {r.get('href', 'No URL')}\n  {r.get('body', 'No description')}\n\n"
        return formatted_results
    except Exception as e:
        return f"Search failed: {str(e)}"
