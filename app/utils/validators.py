import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException, status


def validate_and_sanitize_url(url_str: str) -> str:
    """
    Validates URL format, schemes (http/https only), and prevents SSRF
    by rejecting private, loopback, multicast, and link-local IP addresses.
    """
    try:
        parsed = urlparse(url_str.strip())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid URL structure: {str(e)}",
        )

    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="URL scheme must be http or https.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="URL must contain a valid domain name or hostname.",
        )

    # Disallow localhost by string
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access to internal/localhost addresses is prohibited (SSRF protection).",
        )

    # Resolve IP addresses for hostname and check against private/reserved ranges
    try:
        ip_addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # Domain cannot be resolved
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to resolve domain: '{hostname}'. Please check the URL.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DNS resolution error for domain '{hostname}': {str(e)}",
        )

    for item in ip_addresses:
        ip_str = item[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_reserved
                or ip_obj.is_link_local
                or ip_obj.is_multicast
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access to private or internal IP ranges is prohibited (SSRF protection).",
                )
        except ValueError:
            continue

    return url_str.strip()
