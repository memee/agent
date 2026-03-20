from pathlib import Path

import pytest

from agent.sandbox import FileSandbox, HttpSandbox, SandboxConfig


# ---------------------------------------------------------------------------
# FileSandbox
# ---------------------------------------------------------------------------

def test_file_sandbox_default_construction():
    fs = FileSandbox()
    assert fs.base_dir is None
    assert ".env" in fs.blocked_paths
    assert ".git" in fs.blocked_paths
    assert fs.max_file_bytes == 1_000_000


def test_file_sandbox_default_preset_equals_default_construction():
    assert FileSandbox.default() == FileSandbox()


def test_file_sandbox_strict_sets_base_dir():
    base = Path("/workspace")
    fs = FileSandbox.strict(base)
    assert fs.base_dir == base
    assert fs.max_file_bytes < FileSandbox.default().max_file_bytes
    assert len(fs.blocked_paths) > len(FileSandbox.default().blocked_paths)


def test_file_sandbox_off_disables_all_restrictions():
    fs = FileSandbox.off()
    assert fs.base_dir is None
    assert fs.blocked_paths == []
    assert fs.max_file_bytes > FileSandbox.default().max_file_bytes


# ---------------------------------------------------------------------------
# HttpSandbox
# ---------------------------------------------------------------------------

def test_http_sandbox_default_construction():
    hs = HttpSandbox()
    assert hs.block_private_ips is True
    assert hs.allowed_hosts is None
    assert hs.timeout == 10.0
    assert hs.max_response_bytes == 500_000


def test_http_sandbox_default_preset_equals_default_construction():
    assert HttpSandbox.default() == HttpSandbox()


def test_http_sandbox_strict():
    hs = HttpSandbox.strict()
    assert hs.block_private_ips is True
    assert hs.timeout < HttpSandbox.default().timeout
    assert hs.max_response_bytes < HttpSandbox.default().max_response_bytes


def test_http_sandbox_off_disables_all_restrictions():
    hs = HttpSandbox.off()
    assert hs.block_private_ips is False
    assert hs.timeout > HttpSandbox.default().timeout
    assert hs.max_response_bytes > HttpSandbox.default().max_response_bytes


# ---------------------------------------------------------------------------
# SandboxConfig (composite)
# ---------------------------------------------------------------------------

def test_sandbox_config_default_construction():
    cfg = SandboxConfig()
    assert isinstance(cfg.filesystem, FileSandbox)
    assert isinstance(cfg.http, HttpSandbox)
    assert cfg.filesystem == FileSandbox.default()
    assert cfg.http == HttpSandbox.default()


def test_sandbox_config_default_preset_equals_default_construction():
    assert SandboxConfig.default() == SandboxConfig()


def test_sandbox_config_strict_delegates_to_sub_configs():
    base = Path("/workspace")
    cfg = SandboxConfig.strict(base)
    assert cfg.filesystem == FileSandbox.strict(base)
    assert cfg.http == HttpSandbox.strict()


def test_sandbox_config_off_delegates_to_sub_configs():
    cfg = SandboxConfig.off()
    assert cfg.filesystem == FileSandbox.off()
    assert cfg.http == HttpSandbox.off()


def test_sandbox_config_independent_sub_config_composition():
    base = Path("/workspace")
    cfg = SandboxConfig(
        filesystem=FileSandbox.strict(base),
        http=HttpSandbox.off(),
    )
    assert cfg.filesystem.base_dir == base
    assert cfg.http.block_private_ips is False
