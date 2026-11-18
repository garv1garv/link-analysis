import httpx
from fastapi import HTTPException, status
from typing import Dict, Any

from app.config import settings
from app.utils.validators import validate_and_sanitize_url
from app.utils.text_cleaner import extract_and_clean_html


class WebsiteExtractor:
    def __init__(self):
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)

    async def fetch_and_extract(self, url: str) -> Dict[str, Any]:
        """
        Validates URL (with SSRF check), fetches website HTML asynchronously,
        and extracts cleaned text and metadata.
        """
        sanitized_url = validate_and_sanitize_url(url)

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False,  # Allow self-signed or incomplete cert chains for analysis
        ) as client:
            try:
                response = await client.get(sanitized_url)
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Target website returned error status code: {response.status_code}",
                    )

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    # Proceed with best-effort decode if not strictly binary
                    pass

                raw_html = response.text
                if not raw_html or len(raw_html.strip()) < 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The website returned empty or insufficient content to analyze.",
                    )

                extracted_data = extract_and_clean_html(
                    raw_html, max_chars=settings.MAX_EXTRACTED_CHARS
                )
                extracted_data["final_url"] = str(response.url)
                return extracted_data

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Connection to target website timed out.",
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to connect to target website: {str(exc)}",
                )
