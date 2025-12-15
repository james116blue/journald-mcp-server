#!/usr/bin/env python3
"""
Example usage of the journald MCP server datetime filtering tools.
This script demonstrates how the datetime parsing and journal filtering works.
"""
import sys
sys.path.insert(0, '.')

from journald_mcp_server import datetime_utils

def demonstrate_datetime_parsing():
    """Demonstrate datetime parsing functionality."""
    print("=== Datetime Parsing Examples ===")
    
    examples = [
        "2 hours ago",
        "yesterday at 3pm", 
        "2024-01-15 14:30",
        "now",
        "today at 9am",
        "last week",
        "1 day ago",
        "tomorrow 3pm"
    ]
    
    for example in examples:
        try:
            result = datetime_utils.parse_datetime_input(example)
            print(f"  '{example}' -> {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except ValueError as e:
            print(f"  '{example}' -> ERROR: {e}")
    
    print()

def demonstrate_timestamp_formatting():
    """Demonstrate timestamp formatting functionality."""
    print("=== Timestamp Formatting Examples ===")
    
    from datetime import datetime, timezone
    
    # Test with microseconds timestamp (typical journal format)
    timestamp_us = 1609459200000000  # 2021-01-01 00:00:00 UTC
    
    iso_format = datetime_utils.format_journal_timestamp(timestamp_us)
    human_format = datetime_utils.format_journal_timestamp_human(timestamp_us)
    
    print(f"  Microseconds timestamp: {timestamp_us}")
    print(f"    ISO format: {iso_format}")
    print(f"    Human format: {human_format}")
    
    # Test with datetime object
    dt = datetime(2021, 6, 15, 14, 30, 45, tzinfo=timezone.utc)
    human_format_dt = datetime_utils.format_journal_timestamp_human(dt)
    
    print(f"  Datetime object: {dt}")
    print(f"    Human format: {human_format_dt}")
    
    print()

def demonstrate_tool_usage():
    """Demonstrate how the MCP tools would be used."""
    print("=== MCP Tool Usage Examples ===")
    
    print("Tool: get_journal_entries")
    print("  Parameters:")
    print("    since='2 hours ago'      # Get logs from last 2 hours")
    print("    until='now'              # Up to current time")
    print("    unit='ssh.service'       # Filter by systemd unit")
    print("    limit=50                 # Limit to 50 entries")
    print()
    
    print("Tool: get_recent_logs")
    print("  Parameters:")
    print("    minutes=60               # Last 60 minutes")
    print("    unit='cron.service'      # Filter by unit (optional)")
    print("    limit=20                 # Limit to 20 messages")
    print()
    
    print("Expected output formats:")
    print("  get_journal_entries returns list of dicts with keys:")
    print("    - timestamp: '2024-01-15 14:30:45 UTC'")
    print("    - unit: 'ssh.service' (or empty string)")
    print("    - identifier: 'sshd' (or empty string)")
    print("    - message: 'User login from 192.168.1.1'")
    print()
    
    print("  get_recent_logs returns formatted string:")
    print("    '[2024-01-15 14:30:45 UTC] ssh.service: User login from 192.168.1.1'")
    print("    '[2024-01-15 14:31:00 UTC] cron: Daily backup completed'")

if __name__ == "__main__":
    print("Journald MCP Server - Datetime Filtering Examples")
    print("=" * 60)
    print()
    
    demonstrate_datetime_parsing()
    demonstrate_timestamp_formatting()
    demonstrate_tool_usage()
    
    print()
    print("=" * 60)
    print("Note: These are examples of the functionality.")
    print("Actual journal queries require running the MCP server.")
