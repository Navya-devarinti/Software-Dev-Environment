from __future__ import annotations


def make_citation(title: str, url: str, locator: str) -> dict:
    return {
        "title": title,
        "url": url,
        "locator": locator,
    }
