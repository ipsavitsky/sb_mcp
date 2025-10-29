from typing import Any, Literal
import httpx
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
from argparse import ArgumentParser


@dataclass
class AppContext:
    base_url: str
    api_token: str | None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    parser = ArgumentParser(prog="sb_mcp")
    parser.add_argument("--url", default="https://silverbullet.md")
    parser.add_argument("--token")
    parser.add_argument("--token-file")
    args = parser.parse_args()
    token: str | None = None
    match (args.token, args.token_file):
        case (t, None):
            token = t
        case (None, tf):
            with open(tf, "r") as f:
                token = f.read().strip()
        case (t, tf):
            raise RuntimeError("Specified bot token and token file")
        case (_, _):
            token = None

    yield AppContext(base_url=args.url, api_token=token)


mcp = FastMCP("silverbullet", lifespan=app_lifespan)


async def make_sb_get_request(
    url: str, token: str | None, response_format: Literal["json", "text"] = "json", get_meta: bool = False
) -> tuple[Any | None, dict[str, str]]:
    """Make a GET request to the Silverbullet API with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Sync-Mode": "true"}
            if get_meta:
                headers["X-Get-Meta"] = "true"
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            metadata = {}
            if "X-Last-Modified" in response.headers:
                metadata["last_modified"] = response.headers["X-Last-Modified"]
            if "X-Created" in response.headers:
                metadata["created"] = response.headers["X-Created"]
            if "X-Permission" in response.headers:
                metadata["permission"] = response.headers["X-Permission"]
            if "X-Content-Length" in response.headers:
                metadata["content_length"] = response.headers["X-Content-Length"]
            
            if response_format == "json":
                return response.json(), metadata
            else:
                return response.text, metadata
        except Exception:
            return None, {}


async def make_sb_put_request(url: str, token: str | None, body: str) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Sync-Mode": "true"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = await client.put(
                url, content=body, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            return True
        except Exception:
            return False


async def make_sb_delete_request(url: str, token: str | None) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Sync-Mode": "true"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = await client.delete(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return True
        except Exception:
            return False


@mcp.tool()
async def get_index() -> str:
    """Get the index of all pages"""
    ctx = mcp.get_context()
    base_url = ctx.request_context.lifespan_context.base_url
    token = ctx.request_context.lifespan_context.api_token
    sb_url = f"{base_url}/.fs"
    page_data, _ = await make_sb_get_request(sb_url, token, response_format="json")
    if not isinstance(page_data, list):
        return "Unable to fetch page index"
    valid_pages = []
    for item in page_data:
        if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
            valid_pages.append(item["name"])
    return "\n".join(valid_pages)


@mcp.tool()
async def get_page(page: str) -> str:
    """Get the content of a Silverbullet page.

    Args:
        page: The name of the page to retrieve. Include the `.md` of the page name.
    """
    ctx = mcp.get_context()
    base_url = ctx.request_context.lifespan_context.base_url
    token = ctx.request_context.lifespan_context.api_token
    sb_url = f"{base_url}/.fs/{page}"
    page_data, _ = await make_sb_get_request(sb_url, token, response_format="text")
    return "Unable to fetch page data" if not page_data else page_data


@mcp.tool()
async def write_page(page: str, content: str) -> str:
    """Update the content of a silverbullet page.

    Args:
        page: The name of the page to retrieve. Include the `.md` of the page name.
        content: New content of the page.
    """

    ctx = mcp.get_context()
    base_url = ctx.request_context.lifespan_context.base_url
    token = ctx.request_context.lifespan_context.api_token

    sb_url = f"{base_url}/.fs/{page}"
    success = await make_sb_put_request(sb_url, token, content)
    return (
        "Unable to update page data"
        if not success
        else "Page data updated successfully"
    )


@mcp.tool()
async def delete_page(page: str) -> str:
    """Delete a silverbullet page.

    Args:
        page: The name of the page to delete. Include the `.md` of the page name.
    """

    ctx = mcp.get_context()
    base_url = ctx.request_context.lifespan_context.base_url
    token = ctx.request_context.lifespan_context.api_token

    sb_url = f"{base_url}/.fs/{page}"
    success = await make_sb_delete_request(sb_url, token)
    return (
        "Unable to delete page"
        if not success
        else "Page deleted successfully"
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
