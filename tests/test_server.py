#!/usr/bin/env python3
"""
Tests for journald-mcp-server.
"""
import sys
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from journald_mcp_server import (
    list_journal_units, 
    list_syslog_identifiers, 
    get_first_entry_datetime,
    get_journal_entries,
    get_recent_logs,
    datetime_utils
)


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


def test_get_first_entry_datetime_mocked():
    """Test get_first_entry_datetime with mocked journal."""
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        # Create a mock entry dictionary with get method
        mock_entry = Mock()
        mock_entry.get = Mock(return_value=1609459200000000)  # 2021-01-01 00:00:00 UTC in microseconds
        mock_j.get_next = Mock(return_value=mock_entry)  # Success - returns a mock entry
        mock_reader.return_value = mock_j
        
        result = get_first_entry_datetime()
        # Should now return human-readable format
        assert result == "2021-01-01 00:00:00 UTC"
        mock_j.seek_head.assert_called_once()
        mock_j.get_next.assert_called_once()
        mock_entry.get.assert_called_once_with("__REALTIME_TIMESTAMP")


def test_get_first_entry_datetime_no_entries():
    """Test get_first_entry_datetime when journal is empty."""
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.get_next = Mock(side_effect=StopIteration)  # No entries
        mock_reader.return_value = mock_j
        
        result = get_first_entry_datetime()
        assert result == "No entries found in journal"
        mock_j.seek_head.assert_called_once()
        mock_j.get_next.assert_called_once()


def test_get_first_entry_datetime_no_timestamp():
    """Test get_first_entry_datetime when first entry has no timestamp."""
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        # Create a mock entry dictionary with get method returning None
        mock_entry = Mock()
        mock_entry.get = Mock(return_value=None)  # No timestamp
        mock_j.get_next = Mock(return_value=mock_entry)  # Success
        mock_reader.return_value = mock_j
        
        result = get_first_entry_datetime()
        assert result == "No timestamp found in first entry"
        mock_j.seek_head.assert_called_once()
        mock_j.get_next.assert_called_once()
        mock_entry.get.assert_called_once_with("__REALTIME_TIMESTAMP")


def test_datetime_utils_parse_valid():
    """Test parse_datetime_input with valid inputs."""
    # Test relative time
    result = datetime_utils.parse_datetime_input("2 hours ago")
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    
    # Test absolute time
    result = datetime_utils.parse_datetime_input("2024-01-15 14:30")
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15
    
    # Test "now"
    result = datetime_utils.parse_datetime_input("now")
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc


def test_datetime_utils_parse_invalid():
    """Test parse_datetime_input with invalid inputs."""
    with pytest.raises(ValueError, match="Empty datetime input string"):
        datetime_utils.parse_datetime_input("")
    
    with pytest.raises(ValueError, match="Empty datetime input string"):
        datetime_utils.parse_datetime_input("   ")
    
    with pytest.raises(ValueError, match="Could not parse datetime from input"):
        datetime_utils.parse_datetime_input("not a valid datetime")


def test_datetime_utils_format_timestamp():
    """Test format_journal_timestamp with various inputs."""
    # Test microseconds (int)
    result = datetime_utils.format_journal_timestamp(1609459200000000)
    assert result == "2021-01-01T00:00:00+00:00"
    
    # Test datetime object
    dt = datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = datetime_utils.format_journal_timestamp(dt)
    assert result == "2021-01-01T00:00:00+00:00"
    
    # Test ISO string
    result = datetime_utils.format_journal_timestamp("2021-01-01T00:00:00+00:00")
    assert result == "2021-01-01T00:00:00+00:00"


def test_datetime_utils_format_timestamp_human():
    """Test format_journal_timestamp_human."""
    result = datetime_utils.format_journal_timestamp_human(1609459200000000)
    assert result == "2021-01-01 00:00:00 UTC"


def test_get_journal_entries_mocked():
    """Test get_journal_entries with mocked journal."""
    mock_entries = [
        {
            "__REALTIME_TIMESTAMP": 1609459200000000,
            "_SYSTEMD_UNIT": "ssh.service",
            "SYSLOG_IDENTIFIER": "sshd",
            "MESSAGE": "User login"
        },
        {
            "__REALTIME_TIMESTAMP": 1609459260000000,
            "_SYSTEMD_UNIT": "cron.service",
            "SYSLOG_IDENTIFIER": "cron",
            "MESSAGE": "Job completed"
        },
    ]
    
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.__iter__ = Mock(return_value=iter(mock_entries))
        mock_j.add_match = Mock()
        mock_reader.return_value = mock_j
        
        result = get_journal_entries(since="2 hours ago", limit=2)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["unit"] == "ssh.service"
        assert result[0]["identifier"] == "sshd"
        assert result[0]["message"] == "User login"
        assert result[0]["timestamp"] == "2021-01-01 00:00:00 UTC"


def test_get_journal_entries_invalid_datetime():
    """Test get_journal_entries with invalid datetime input."""
    result = get_journal_entries(since="not a valid datetime")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["timestamp"] == "ERROR"
    assert "Error parsing datetime input" in result[0]["message"]


def test_get_recent_logs_mocked():
    """Test get_recent_logs with mocked journal."""
    mock_entries = [
        {
            "__REALTIME_TIMESTAMP": 1609459200000000,
            "_SYSTEMD_UNIT": "ssh.service",
            "SYSLOG_IDENTIFIER": "sshd",
            "MESSAGE": "User login"
        },
    ]
    
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.__iter__ = Mock(return_value=iter(mock_entries))
        mock_j.add_match = Mock()
        mock_reader.return_value = mock_j
        
        result = get_recent_logs(minutes=60, limit=1)
        
        assert isinstance(result, str)
        assert "2021-01-01 00:00:00 UTC" in result
        assert "ssh.service" in result
        assert "User login" in result


def test_get_recent_logs_no_logs():
    """Test get_recent_logs when no logs are found."""
    with patch("journald_mcp_server.server.journal.Reader") as mock_reader:
        mock_j = Mock()
        mock_j.__iter__ = Mock(return_value=iter([]))
        mock_j.add_match = Mock()
        mock_reader.return_value = mock_j
        
        result = get_recent_logs(minutes=60)
        assert "No logs found in the last 60 minutes" in result


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
