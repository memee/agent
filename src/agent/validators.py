from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from agent.sandbox import FileSandbox, HttpSandbox

Validator = Callable[[Any, Any], Any]


def file_path_validator(value: Any, sandbox: FileSandbox) -> Path:
    """Resolve path, enforce base_dir and blocked_paths. Returns absolute Path."""
    path = Path(value).resolve()

    if sandbox.base_dir is not None:
        base = sandbox.base_dir.resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise PermissionError(f"Path '{path}' is outside base_dir '{base}'")

    for pattern in sandbox.blocked_paths:
        if path.match(pattern):
            raise PermissionError(f"Path '{path}' matches blocked pattern '{pattern}'")

    return path


def http_url_validator(value: Any, sandbox: HttpSandbox) -> str:
    """Validate URL scheme, allowed_hosts, and private IPs. Returns original URL."""
    url = str(value)
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed; use http or https")

    hostname = parsed.hostname
    if hostname is None:
        raise ValueError(f"URL '{url}' has no hostname")

    if sandbox.allowed_hosts is not None and hostname not in sandbox.allowed_hosts:
        raise PermissionError(f"Host '{hostname}' is not in allowed_hosts")

    if sandbox.block_private_ips:
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise PermissionError(f"URL '{url}' resolves to private IP '{ip_str}'")
        except socket.gaierror:
            raise PermissionError(f"Could not resolve hostname '{hostname}'")

    return url
