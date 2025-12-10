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
    units = {entry.get("_SYSTEMD_UNIT") for entry in j}
    return list(units)

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
@click.option("--port", default=3002, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(port: int, log_level: str) -> int:
    """Run the MCP Everything Server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    logger.info(f"Starting journald MCP  Server on port {port}")
    logger.info(f"Endpoint will be: http://localhost:{port}/mcp")

    mcp.settings.port = port
    mcp.run(transport="streamable-http")

    return 0


if __name__ == "__main__":
    main()