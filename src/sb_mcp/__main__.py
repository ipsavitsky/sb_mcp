from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("silverbullet")

SB_API_BASE = "https://silverbullet.md"

async def make_sb_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Silverbullet API with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={"X-Sync-Mode": "true"}, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_index() -> str:
    """Get the index of all pages"""
    sb_url = f"{SB_API_BASE}/index.json"
    page_data = await make_sb_request(sb_url)
    if not page_data:
        return None
    pages = map(lambda x: x["name"], page_data)
    return "\n".join(pages)
        
@mcp.tool()
async def get_page(page: str) -> str:
    """Get weather forecast for a location.

    Args:
        page: page name
    """
    sb_url = f"{SB_API_BASE}/{page}"
    page_data = await make_sb_request(sb_url)

    return "Unable to fetch forecast data for this location." if not page_data else page_data

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
