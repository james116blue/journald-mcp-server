#!/usr/bin/env python3
"""
Journald MCP server
"""
import sys
import logging
import click
from mcp.server.fastmcp import  FastMCP
from systemd import journal
from datetime import datetime, timedelta
from itertools import islice

from typing import List

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="journald-mcp-server"
)

# Resources
@mcp.resource("journal://units")
def list_journal_units() -> List[str]:
    """Collects unique systemd units from the journald logs for last 30 minutes"""
    j = journal.Reader()
    j.seek_realtime(datetime.now() - timedelta(minutes=30))
    units = {entry.get("_SYSTEMD_UNIT") for entry in j if entry.get("_SYSTEMD_UNIT")}
    return list(units)

@mcp.resource("journal://syslog-identifiers")
def list_syslog_identifiers() -> List[str]:
    """Collects unique syslog identifiers from the journald logs for last 30 minutes"""
    j = journal.Reader()
    j.seek_realtime(datetime.now() - timedelta(minutes=30))
    identifiers = {entry.get("SYSLOG_IDENTIFIER") for entry in j if entry.get("SYSLOG_IDENTIFIER")}
    return list(identifiers)

# Tools
# @mcp.tool()
# def get_last_log(n_minutes: int, n_messages: int) -> str:
#     """Show n_messages from journald logs for last n_minutes minutes"""
#     logger.info(f"Requested {n_messages} rtkit-daemonsh logs for last {n_minutes} minutes")
#     j = journal.Reader()
#     j.seek_realtime(datetime.now() - timedelta(minutes=n_minutes))
#     messages = '\n'.join([event['MESSAGE'] for event in islice(j, n_messages)])
#     return messages

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
