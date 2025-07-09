import os
from typing import Any, Literal
import httpx
from mcp.server.elicitation import AcceptedElicitation, CancelledElicitation, DeclinedElicitation
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

mcp = FastMCP("silverbullet")

SB_API_BASE = os.getenv("SB_API_BASE_URL", "https://silverbullet.md")
SB_API_TOKEN = os.getenv("SB_API_TOKEN")

async def make_sb_get_request(url: str, response_format: Literal['json', 'text'] = 'json') -> Any | None:
    """Make a request to the Silverbullet API with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Sync-Mode": "true"}
            if SB_API_TOKEN:
                headers["Authorization"] = f"Token {SB_API_TOKEN}"
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            if response_format == 'json':
                return response.json()
            else:
                return response.text
        except Exception:
            return None

async def make_sb_put_request(url: str, body: str) -> bool | None:
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Sync-Mode": "true"}
            if SB_API_TOKEN:
                headers["Authorization"] = f"Token {SB_API_TOKEN}"
            response = await client.put(url, content=body, headers=headers, timeout=30.0)
            response.raise_for_status()
            return True
        except Exception:
            return None

@mcp.tool()
async def get_silverbullet_index() -> str:
    """Get the index of all pages"""
    sb_url = f"{SB_API_BASE}/index.json"
    page_data = await make_sb_get_request(sb_url, response_format='json')
    if not isinstance(page_data, list):
        return "Unable to fetch page index"
    valid_pages = []
    for item in page_data:
        if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
            valid_pages.append(item["name"])
    return "\n".join(valid_pages)

@mcp.resource("silverbullet://{page}")
async def get_silverbullet_page(page: str) -> str:
    """Get the content of a Silverbullet page.

    Args:
        page: The name of the page to retrieve. Include the `.md` of the page name.
    """
    sb_url = f"{SB_API_BASE}/{page}"
    page_data = await make_sb_get_request(sb_url, response_format='text')
    return "Unable to fetch page data" if not page_data else page_data

@mcp.tool()
async def write_silverbullet_page(page: str, content: str, ctx: Context) -> str:
    """Update the content of a silverbullet page.

    Args:
        page: The name of the page to retrieve. Include the `.md` of the page name.
        content: New content of the page.
    """

    class ConfirmWrite(BaseModel):
        confirm: bool = Field(description="Confirm write?")

    result = await ctx.elicit(
        message=f"Write the following text to {page}? (WARNING! THIS WILL OVERRIDE THE CURRENT PAGE)\n{content}",
        schema=ConfirmWrite
    )
    match result:
        case AcceptedElicitation():
            # Proceed with the write operation
            sb_url = f"{SB_API_BASE}/{page}"
            page_data = await make_sb_put_request(sb_url, content)
            return "Unable to update page data" if not page_data else "Page data updated successfully"
        case DeclinedElicitation():
            return "Write declined"
        case CancelledElicitation():
            return "Write cancelled"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
