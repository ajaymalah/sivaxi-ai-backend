from dotenv import load_dotenv

load_dotenv()

import os

from langchain_core.tools import tool
import requests


@tool
def search_web(query: str):
    """Search the internet using SearXNG."""

    try:
        response = requests.get(
            os.getenv("SEARXNG_URL"),
            params={
                "q": query,
                "format": "json"
            },
            timeout=30
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:

        return (
            "WEB_SEARCH_ERROR\n"
            f"Error: {error}\n"
            f"Query: {query}"
        )

