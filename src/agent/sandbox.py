from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileSandbox:
    base_dir: Path | None = None
    blocked_paths: list[str] = field(default_factory=lambda: [".env", ".git"])
    max_file_bytes: int = 1_000_000

    @classmethod
    def default(cls) -> "FileSandbox":
        return cls()

    @classmethod
    def strict(cls, base_dir: Path) -> "FileSandbox":
        return cls(
            base_dir=base_dir,
            blocked_paths=[".env", ".git", "*.key", "*.pem"],
            max_file_bytes=100_000,
        )

    @classmethod
    def off(cls) -> "FileSandbox":
        return cls(
            base_dir=None,
            blocked_paths=[],
            max_file_bytes=100_000_000,
        )


@dataclass
class HttpSandbox:
    block_private_ips: bool = True
    allowed_hosts: list[str] | None = None
    timeout: float = 10.0
    max_response_bytes: int = 500_000

    @classmethod
    def default(cls) -> "HttpSandbox":
        return cls()

    @classmethod
    def strict(cls) -> "HttpSandbox":
        return cls(
            block_private_ips=True,
            allowed_hosts=None,
            timeout=5.0,
            max_response_bytes=100_000,
        )

    @classmethod
    def off(cls) -> "HttpSandbox":
        return cls(
            block_private_ips=False,
            allowed_hosts=None,
            timeout=60.0,
            max_response_bytes=100_000_000,
        )


@dataclass
class SandboxConfig:
    filesystem: FileSandbox = field(default_factory=FileSandbox)
    http: HttpSandbox = field(default_factory=HttpSandbox)

    @classmethod
    def default(cls) -> "SandboxConfig":
        return cls()

    @classmethod
    def strict(cls, file_base_dir: Path) -> "SandboxConfig":
        return cls(
            filesystem=FileSandbox.strict(file_base_dir),
            http=HttpSandbox.strict(),
        )

    @classmethod
    def off(cls) -> "SandboxConfig":
        return cls(
            filesystem=FileSandbox.off(),
            http=HttpSandbox.off(),
        )
