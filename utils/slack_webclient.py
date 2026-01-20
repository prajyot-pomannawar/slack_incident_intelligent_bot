"""
Slack WebClient construction for corporate network environments.

This module builds a Slack `WebClient` with an explicit SSL context so you can trust a corporate CA bundle
or force specific TLS versions when proxies/SSL interception cause handshake issues.
"""

import os
import ssl
from typing import Optional, Union

import certifi
from slack_sdk.web.client import WebClient


def _get_ca_bundle() -> Optional[str]:
    """
    Return a CA bundle path to trust corporate TLS interception if needed.

    Supported env vars (first match wins):
      - SLACK_CA_BUNDLE
      - REQUESTS_CA_BUNDLE
    """
    for k in ("SLACK_CA_BUNDLE", "REQUESTS_CA_BUNDLE"):
        v = (os.environ.get(k) or "").strip()
        if v:
            return v
    return None


def _tls_version(v: str) -> Optional[ssl.TLSVersion]:
    v = (v or "").strip().lower()
    if v in {"1.2", "tls1.2", "tlsv1.2"}:
        return ssl.TLSVersion.TLSv1_2
    if v in {"1.3", "tls1.3", "tlsv1.3"}:
        return ssl.TLSVersion.TLSv1_3
    return None


def build_slack_web_client(token: str) -> WebClient:
    """
    Create a Slack WebClient with an explicit SSL context.

    Why:
      Some corporate networks / proxies cause urllib SSL handshake failures.
      Using an explicit CA bundle (or forcing TLS 1.2) can stabilize calls like views.open.
    """
    cafile = _get_ca_bundle() or certifi.where()
    ctx = ssl.create_default_context(cafile=cafile)

    # Optional: force TLS min/max to avoid proxy issues with TLS1.3
    min_v = _tls_version(os.environ.get("SLACK_TLS_MIN", ""))
    max_v = _tls_version(os.environ.get("SLACK_TLS_MAX", ""))
    if min_v:
        ctx.minimum_version = min_v
    if max_v:
        ctx.maximum_version = max_v

    return WebClient(token=token, ssl=ctx)

