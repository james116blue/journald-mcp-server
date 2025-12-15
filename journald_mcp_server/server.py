#!/usr/bin/env python3
"""
Journald MCP server
"""
import sys
import logging
import click
from mcp.server.fastmcp import FastMCP
from systemd import journal
from datetime import datetime, timedelta, timezone
from itertools import islice
from typing import List, Dict, Optional

from journald_mcp_server import datetime_utils

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="journald-mcp-server"
)

# Resources
@mcp.resource("journal://units")
def list_journal_units() -> List[str]:
    """Collects unique systemd units from the journald logs"""
    j = journal.Reader()
    units = {entry.get("_SYSTEMD_UNIT") for entry in j if entry.get("_SYSTEMD_UNIT")}
    return list(units)
 
@mcp.resource("journal://syslog-identifiers")
def list_syslog_identifiers() -> List[str]:
    """Collects unique syslog identifiers from the journald logs"""
    j = journal.Reader()
    identifiers = {entry.get("SYSLOG_IDENTIFIER") for entry in j if entry.get("SYSLOG_IDENTIFIER")}
    return list(identifiers)

@mcp.resource("journal://first-entry-datetime")
def get_first_entry_datetime() -> str:
    """Returns the datetime of the first entry in the journal"""
    j = journal.Reader()
    j.seek_head()  # Go to the beginning of the journal
    try:
        entry = j.get_next()
    except StopIteration:
        return "No entries found in journal"
    
    # Get the timestamp from the first entry
    timestamp_val = entry.get("__REALTIME_TIMESTAMP")
    if timestamp_val:
        try:
            # Use datetime_utils to format the timestamp
            return datetime_utils.format_journal_timestamp_human(timestamp_val)
        except ValueError as e:
            return f"Error formatting timestamp: {str(e)}"
    else:
        return "No timestamp found in first entry"

# Tools
@mcp.tool()
def get_journal_entries(
    since: Optional[str] = None,
    until: Optional[str] = None,
    unit: Optional[str] = None,
    identifier: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, str]]:
    """
    Get journal entries with datetime filtering.
    
    Supports filtering by time range (since/until), systemd unit, and syslog identifier.
    
    Args:
        since: Start datetime (e.g., "2 hours ago", "2024-01-15 14:30")
        until: End datetime (e.g., "now", "1 hour ago", "2024-01-15 15:30")
        unit: Filter by systemd unit name
        identifier: Filter by syslog identifier
        limit: Maximum number of entries to return (default: 100)
        
    Returns:
        List of journal entries with timestamp, unit, identifier, and message
    """
    try:
        # Parse datetime inputs
        since_dt = None
        if since:
            since_dt = datetime_utils.parse_datetime_input(since)
            
        until_dt = None
        if until:
            until_dt = datetime_utils.parse_datetime_input(until)
        
        # Create journal reader
        j = journal.Reader()
        
        # Apply time filtering
        if since_dt:
            j.seek_realtime(since_dt)
        
        # Apply additional filters
        if unit:
            j.add_match(_SYSTEMD_UNIT=unit)
        if identifier:
            j.add_match(SYSLOG_IDENTIFIER=identifier)
        
        # Collect entries
        entries = []
        for entry in islice(j, limit):
            # Apply until filter if specified
            if until_dt:
                timestamp_val = entry.get("__REALTIME_TIMESTAMP")
                if timestamp_val:
                    try:
                        if timestamp_val > until_dt:
                            break
                    except (ValueError, TypeError):
                        # Skip entries with invalid timestamps
                        continue
            
            # Format the entry
            formatted_entry = {
                "timestamp": datetime_utils.format_journal_timestamp_human(
                    entry.get("__REALTIME_TIMESTAMP", "")
                ),
                "unit": entry.get("_SYSTEMD_UNIT", ""),
                "identifier": entry.get("SYSLOG_IDENTIFIER", ""),
                "message": entry.get("MESSAGE", "")
            }
            entries.append(formatted_entry)
        
        return entries
        
    except ValueError as e:
        # Return error as a single entry for consistency
        return [{
            "timestamp": "ERROR",
            "unit": "",
            "identifier": "",
            "message": f"Error parsing datetime input: {str(e)}"
        }]
    except Exception as e:
        logger.error(f"Error getting journal entries: {e}", exc_info=True)
        return [{
            "timestamp": "ERROR",
            "unit": "",
            "identifier": "",
            "message": f"Internal error: {str(e)}"
        }]


@mcp.tool()
def get_recent_logs(
    minutes: int = 60,
    unit: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Get recent journal logs from the last N minutes.
    
    Args:
        minutes: Number of minutes to look back (default: 60)
        unit: Filter by systemd unit name
        limit: Maximum number of messages to return (default: 50)
        
    Returns:
        Formatted string of recent log messages
    """
    try:
        # Calculate since time
        since_dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        # Create journal reader
        j = journal.Reader()
        j.seek_realtime(since_dt)
        
        if unit:
            j.add_match(_SYSTEMD_UNIT=unit)
        
        # Collect messages
        messages = []
        for entry in islice(j, limit):
            timestamp = datetime_utils.format_journal_timestamp_human(
                entry.get("__REALTIME_TIMESTAMP", "")
            )
            unit_name = entry.get("_SYSTEMD_UNIT", "")
            identifier = entry.get("SYSLOG_IDENTIFIER", "")
            message = entry.get("MESSAGE", "")
            
            messages.append(f"[{timestamp}] {unit_name or identifier}: {message}")
        
        if not messages:
            return f"No logs found in the last {minutes} minutes"
        
        return "\n".join(messages)
        
    except Exception as e:
        logger.error(f"Error getting recent logs: {e}", exc_info=True)
        return f"Error getting recent logs: {str(e)}"

# CLI
@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport protocol to use (stdio, sse, or streamable-http)",
)
@click.option(
    "--port", 
    default=3002, 
    help="Port to listen on for HTTP transport (ignored for stdio transport)"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(transport: str, port: int, log_level: str) -> int:
    """Run the Journald MCP Server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    if transport in ["sse", "streamable-http"]:
        logger.info(f"Starting journald MCP Server with {transport} transport on port {port}")
        logger.info(f"Endpoint will be: http://localhost:{port}/mcp")
        mcp.settings.port = port
    else:
        logger.info(f"Starting journald MCP Server with {transport} transport")

    mcp.run(transport=transport)

    return 0


if __name__ == "__main__":
    main()
