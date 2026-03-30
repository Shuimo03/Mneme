"""Network runtime helpers."""

from __future__ import annotations

import os

import httpx

PROXY_ENV_VARS = (
    "ALL_PROXY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "all_proxy",
    "http_proxy",
    "https_proxy",
    "no_proxy",
)


def disable_proxy_env() -> None:
    """Clear inherited proxy settings so app traffic stays deterministic."""
    for name in PROXY_ENV_VARS:
        os.environ.pop(name, None)


def create_async_http_client(
    *,
    timeout: float = 20.0,
    follow_redirects: bool = True,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    """Create an AsyncClient that never inherits system proxy settings."""
    disable_proxy_env()
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        trust_env=False,
        headers=headers,
    )


def browser_extra_args() -> list[str]:
    """Return browser flags that keep automation traffic independent from host proxy state."""
    return [
        "--no-proxy-server",
        "--proxy-server=direct://",
        "--proxy-bypass-list=*",
    ]
