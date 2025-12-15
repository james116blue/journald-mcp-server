#!/usr/bin/env python3
"""
Tests for journald-mcp-server.
"""
import sys
import pytest
from unittest.mock import Mock, patch
from journald_mcp_server import list_journal_units, list_syslog_identifiers


def test_list_journal_units_mocked():
    """Test list_journal_units with mocked journal."""
    mock_entries = [
        {"_SYSTEMD_UNIT": "ssh.service"},
        {"_SYSTEMD_UNIT": "nginx.service"},
        {"_SYSTEMD_UNIT": "ssh.service"},  # duplicate
        {},  # missing unit
    ]
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.__iter__ = Mock(return_value=iter(mock_entries))
        mock_reader.return_value = mock_j
        result = list_journal_units()
        assert isinstance(result, list)
        assert set(result) == {"ssh.service", "nginx.service"}
        # Ensure seek_realtime was called
        mock_j.seek_realtime.assert_called_once()


def test_list_syslog_identifiers_mocked():
    """Test list_syslog_identifiers with mocked journal."""
    mock_entries = [
        {"SYSLOG_IDENTIFIER": "sshd"},
        {"SYSLOG_IDENTIFIER": "cron"},
        {"SYSLOG_IDENTIFIER": "sshd"},  # duplicate
        {},  # missing identifier
        {"SYSLOG_IDENTIFIER": "dbus"},
    ]
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.__iter__ = Mock(return_value=iter(mock_entries))
        mock_reader.return_value = mock_j
        result = list_syslog_identifiers()
        assert isinstance(result, list)
        assert set(result) == {"sshd", "cron", "dbus"}
        mock_j.seek_realtime.assert_called_once()


def test_main_cli():
    """Test that main can be invoked (smoke test)."""
    from journald_mcp_server import main
    # main is a click command, we can invoke it with --help
    import click.testing
    runner = click.testing.CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
