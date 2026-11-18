import pytest
from fastapi import HTTPException
from app.utils.validators import validate_and_sanitize_url
from app.utils.text_cleaner import extract_and_clean_html


def test_ssrf_protection_localhost():
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_url("http://localhost:8000")
    assert exc_info.value.status_code == 400
    assert "SSRF" in exc_info.value.detail or "internal" in exc_info.value.detail


def test_ssrf_protection_loopback_ip():
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_url("http://127.0.0.1:4000/secret")
    assert exc_info.value.status_code == 400


def test_invalid_scheme():
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_url("ftp://ftp.example.com")
    assert exc_info.value.status_code == 422


def test_valid_public_domain():
    url = "https://example.com"
    validated = validate_and_sanitize_url(url)
    assert validated == url


def test_html_cleaner():
    raw_html = """
    <html>
        <head>
            <title>Test Business - High Tech Solutions</title>
            <meta name="description" content="We build advanced cloud software." />
        </head>
        <body>
            <script>alert("hack");</script>
            <style>body { color: red; }</style>
            <header><nav>Home | Contact</nav></header>
            <h1>Leading Cloud Solutions</h1>
            <h2>Scalable Infrastructure</h2>
            <p>Our company offers 24/7 cloud management and DevOps engineering services.</p>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    result = extract_and_clean_html(raw_html)
    assert result["title"] == "Test Business - High Tech Solutions"
    assert result["meta_description"] == "We build advanced cloud software."
    assert "H1: Leading Cloud Solutions" in result["headings"]
    assert "H2: Scalable Infrastructure" in result["headings"]
    assert "Leading Cloud Solutions" in result["cleaned_text"]
    assert "alert" not in result["cleaned_text"]
    assert "Copyright" not in result["cleaned_text"]
