from pathlib import Path
from unittest.mock import patch

import pytest

from agent.sandbox import FileSandbox, HttpSandbox
from agent.validators import file_path_validator, http_url_validator


# ---------------------------------------------------------------------------
# file_path_validator
# ---------------------------------------------------------------------------

def test_file_path_within_base_dir_is_allowed(tmp_path):
    sandbox = FileSandbox(base_dir=tmp_path, blocked_paths=[])
    target = tmp_path / "src" / "main.py"
    target.parent.mkdir(parents=True)
    target.touch()
    result = file_path_validator(str(target), sandbox)
    assert result == target.resolve()


def test_file_path_traversal_outside_base_dir_is_blocked(tmp_path):
    sandbox = FileSandbox(base_dir=tmp_path, blocked_paths=[])
    outside_path = str(tmp_path / ".." / "etc" / "passwd")
    with pytest.raises(PermissionError):
        file_path_validator(outside_path, sandbox)


def test_file_path_blocked_pattern_is_rejected(tmp_path):
    sandbox = FileSandbox(base_dir=None, blocked_paths=[".env"])
    env_file = tmp_path / ".env"
    env_file.touch()
    with pytest.raises(PermissionError):
        file_path_validator(str(env_file), sandbox)


def test_file_path_no_base_dir_allows_any_path(tmp_path):
    sandbox = FileSandbox(base_dir=None, blocked_paths=[])
    target = tmp_path / "notes.txt"
    target.touch()
    result = file_path_validator(str(target), sandbox)
    assert result == target.resolve()


def test_file_path_returns_absolute_path(tmp_path):
    sandbox = FileSandbox(base_dir=tmp_path, blocked_paths=[])
    target = tmp_path / "file.txt"
    target.touch()
    result = file_path_validator(str(target), sandbox)
    assert result.is_absolute()


# ---------------------------------------------------------------------------
# http_url_validator
# ---------------------------------------------------------------------------

def test_http_url_public_url_allowed():
    sandbox = HttpSandbox(block_private_ips=True, allowed_hosts=None)
    with patch("socket.gethostbyname", return_value="93.184.216.34"):
        result = http_url_validator("https://api.example.com/data", sandbox)
    assert result == "https://api.example.com/data"


def test_http_url_private_ip_blocked():
    sandbox = HttpSandbox(block_private_ips=True)
    with pytest.raises(PermissionError):
        http_url_validator("http://169.254.169.254/latest/meta-data/", sandbox)


def test_http_url_loopback_blocked():
    sandbox = HttpSandbox(block_private_ips=True)
    with pytest.raises(PermissionError):
        http_url_validator("http://127.0.0.1/admin", sandbox)


def test_http_url_non_allowed_host_blocked():
    sandbox = HttpSandbox(block_private_ips=False, allowed_hosts=["api.example.com"])
    with pytest.raises(PermissionError):
        http_url_validator("https://other.com/data", sandbox)


def test_http_url_non_http_scheme_rejected():
    sandbox = HttpSandbox(block_private_ips=False)
    with pytest.raises(ValueError):
        http_url_validator("file:///etc/passwd", sandbox)


def test_http_url_ftp_scheme_rejected():
    sandbox = HttpSandbox(block_private_ips=False)
    with pytest.raises(ValueError):
        http_url_validator("ftp://example.com/file", sandbox)


def test_http_url_private_ip_check_disabled():
    sandbox = HttpSandbox(block_private_ips=False)
    result = http_url_validator("http://192.168.1.1/page", sandbox)
    assert result == "http://192.168.1.1/page"
