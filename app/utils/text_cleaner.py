import re
from bs4 import BeautifulSoup
from typing import Dict, Any


def extract_and_clean_html(html_content: str, max_chars: int = 15000) -> Dict[str, Any]:
    """
    Extracts semantic meta tags, headings, and clean readable text from raw HTML,
    stripping unnecessary scripts, styles, SVGs, and boilerplate.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract Meta Tags
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_keywords = ""
    og_title = ""
    og_desc = ""

    for tag in soup.find_all("meta"):
        name = tag.get("name", "").lower()
        prop = tag.get("property", "").lower()
        content = tag.get("content", "").strip()

        if name == "description" and not meta_desc:
            meta_desc = content
        elif name == "keywords" and not meta_keywords:
            meta_keywords = content
        elif prop == "og:title" and not og_title:
            og_title = content
        elif prop == "og:description" and not og_desc:
            og_desc = content

    # Extract Key Headings (H1, H2, H3)
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text and len(text) > 2:
            headings.append(f"{h.name.upper()}: {text}")

    # Remove unwanted tags
    for tag_name in ["script", "style", "noscript", "svg", "iframe", "nav", "footer", "form", "button", "header"]:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Extract clean text from body
    body_text = soup.get_text(separator=" ", strip=True)
    body_text = re.sub(r"\s+", " ", body_text)

    # Budget text length for LLM token optimization
    truncated_text = body_text[:max_chars]

    return {
        "title": title or og_title,
        "meta_description": meta_desc or og_desc,
        "meta_keywords": meta_keywords,
        "headings": headings[:30],  # top 30 headings
        "cleaned_text": truncated_text,
    }

