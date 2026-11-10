"""JobShield AI — SSRF-Safe URL Fetcher.

Fetches public job posting pages with robust Server-Side Request Forgery (SSRF)
protections, DNS resolution validation, private IP blocking, redirect re-validation,
strict response size limits, and safe timeouts.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse, urljoin
import httpx

logger = logging.getLogger("jobshield.extraction.url_fetcher")

# Prohibited destination IP networks (RFC 1918, RFC 3927, loopback, cloud metadata)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::/128"),               # IPv6 loopback / unspecified
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),             # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),            # IPv6 Link-Local
]

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 JobShieldAI-Bot/1.0"
)


class SSRFValidationError(ValueError):
    """Raised when a destination URL attempts to access prohibited internal or private network resources."""
    pass


class HttpRetrievalError(Exception):
    """Raised when an HTTP request returns a non-200 status that the caller should handle specifically.

    Attributes:
        status_code: The HTTP status code returned by the server.
        extraction_status: Machine-readable extraction status string for the ExtractionResponse.
        user_message: Safe, human-readable message suitable for display in the UI.
    """

    def __init__(self, status_code: int, extraction_status: str, user_message: str) -> None:
        self.status_code = status_code
        self.extraction_status = extraction_status
        self.user_message = user_message
        super().__init__(user_message)


def validate_ip_address(ip_str: str) -> None:
    """Validate that resolved IP address does not fall within private or restricted blocks."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        raise SSRFValidationError("Invalid IP address format.")

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise SSRFValidationError("Destination IP address is reserved or internal.")

    for net in BLOCKED_NETWORKS:
        if ip in net:
            raise SSRFValidationError("Access to private/internal network addresses is prohibited.")


def validate_url_security(url: str) -> str:
    """Validate URL scheme, structure, and hostname resolution against SSRF attacks."""
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError(f"Unsupported protocol scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL is missing a valid destination hostname.")

    # Reject direct localhost or special local domains
    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal") or lower_host.endswith(".local") or lower_host.endswith(".internal"):
        raise SSRFValidationError("Access to localhost and internal domain names is prohibited.")

    # Resolve hostname to actual IP addresses and verify every candidate IP
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            validate_ip_address(ip_str)
    except socket.gaierror as e:
        raise SSRFValidationError(f"Hostname resolution failed: {e}")

    return url.strip()


def fetch_url_content(
    url: str,
    timeout_seconds: int = 10,
    max_bytes: int = 2 * 1024 * 1024,
    max_redirects: int = 3,
) -> tuple[str, str]:
    """Fetch publicly accessible HTML content safely with redirect re-validation."""
    current_url = validate_url_security(url)
    redirect_count = 0

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    client = httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=False,
        headers=headers,
        verify=True,
    )

    try:
        while True:
            validate_url_security(current_url)

            try:
                response = client.get(current_url)
            except httpx.TimeoutException:
                raise HttpRetrievalError(
                    status_code=0,
                    extraction_status="RETRIEVAL_FAILED",
                    user_message=(
                        "The website did not respond within the allowed time. "
                        "The server may be temporarily unavailable. Please try again later."
                    ),
                )
            except httpx.ConnectError:
                raise HttpRetrievalError(
                    status_code=0,
                    extraction_status="RETRIEVAL_FAILED",
                    user_message=(
                        "Could not connect to the target website. "
                        "Please verify the URL is correct and the site is accessible."
                    ),
                )

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SSRFValidationError("Too many redirects encountered while fetching posting.")

                location = response.headers.get("Location")
                if not location:
                    raise SSRFValidationError("Redirect response missing Location header.")

                current_url = urljoin(current_url, location)
                continue

            if response.status_code != 200:
                sc = response.status_code
                if sc in (401, 403):
                    raise HttpRetrievalError(
                        status_code=sc,
                        extraction_status="ACCESS_RESTRICTED",
                        user_message=(
                            "Website access was restricted. This website does not allow automated extraction. "
                            "Please copy and paste the job description text directly."
                        ),
                    )
                if sc == 404:
                    raise HttpRetrievalError(
                        status_code=sc,
                        extraction_status="RETRIEVAL_FAILED",
                        user_message=(
                            "The requested job posting page could not be found (404). "
                            "Please verify the URL is correct and the posting is still live."
                        ),
                    )
                if sc == 429:
                    raise HttpRetrievalError(
                        status_code=sc,
                        extraction_status="ACCESS_RESTRICTED",
                        user_message=(
                            "The website is temporarily limiting automated requests (rate limited). "
                            "Please try again later or paste the job description text directly."
                        ),
                    )
                if 500 <= sc < 600:
                    raise HttpRetrievalError(
                        status_code=sc,
                        extraction_status="RETRIEVAL_FAILED",
                        user_message=(
                            f"The website returned a server error ({sc}). "
                            "This is a temporary issue on the target site. Please try again later."
                        ),
                    )
                raise HttpRetrievalError(
                    status_code=sc,
                    extraction_status="RETRIEVAL_FAILED",
                    user_message=f"HTTP request failed with status code {sc} ({response.reason_phrase}).",
                )

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValueError(f"Page content exceeds maximum allowed size ({max_bytes} bytes).")

            content_bytes = response.content
            if len(content_bytes) > max_bytes:
                content_bytes = content_bytes[:max_bytes]

            encoding = response.encoding or "utf-8"
            html_text = content_bytes.decode(encoding, errors="replace")
            return html_text, current_url

    finally:
        client.close()
