# Journald MCP Server

An MCP server for accessing systemd journal logs.

## Features

- List systemd units from journal logs
- List syslog identifiers from journal logs
- Get datetime of first journal entry
- Filter journal entries by datetime range (since/until)
- Filter by systemd unit or syslog identifier
- Filter by message content (case-insensitive substring matching)
- Natural language datetime parsing (e.g., "2 hours ago", "yesterday at 3pm")
- List units and identifiers within specific time ranges

## Installation


```bash
# Install dependencies
uv sync
```

## Usage
Run as non-root: Give the user systemd-journal group access  `usermod -aG systemd-journal $USER`

Run the server with:

```bash
uv run server.py [OPTIONS]
```

### CLI Options

- `--transport`: Transport protocol to use (`stdio`, `sse`, or `streamable-http`). Default: `stdio`
- `--port`: Port to listen on for HTTP transport (ignored for `stdio` transport). Default: `3002`
- `--log-level`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default: `INFO`

### Examples

1. Run with stdio transport (default, for MCP clients that communicate via stdin/stdout):
   ```bash
   python server.py
   ```

2. Run with HTTP transport on custom port:
   ```bash
   python server.py --transport streamable-http --port 8080
   ```

3. Run with SSE transport:
   ```bash
   python server.py --transport sse --port 3000
   ```

4. Run with debug logging:
   ```bash
   python server.py --log-level DEBUG
   ```

## MCP Integration

The server provides the following MCP resources and tools:

### Resources
- `journal://units`: List unique systemd units from journal logs (all accessible time)
- `journal://syslog-identifiers`: List unique syslog identifiers from journal logs (all accessible time)
- `journal://first-entry-datetime`: Get the datetime of the first entry in the journal
- `journal://units/{since}/{until}`: List unique systemd units within a specified time range
- `journal://syslog-identifiers/{since}/{until}`: List unique syslog identifiers within a specified time range

### Tools
- `get_journal_entries`: Get journal entries with datetime filtering
  - Parameters: `since` (optional), `until` (optional), `unit` (optional), `identifier` (optional), `message_contains` (optional), `limit` (default: 100)
  - Returns: List of entries with timestamp, unit, identifier, and message
  - Example: Get logs from last 2 hours containing "error": `since="2 hours ago", message_contains="error"`
  
- `get_recent_logs`: Get recent journal logs from the last N minutes
  - Parameters: `minutes` (default: 60), `unit` (optional), `limit` (default: 50)
  - Returns: Formatted string of recent log messages

### Datetime Input Format
The server uses natural language datetime parsing via the `dateparser` library. Supported formats include:
- Relative times: "2 hours ago", "yesterday at 3pm", "last week", "now"
- Absolute times: "2024-01-15 14:30", "2024-01-15T14:30:00"
- Mixed: "today at 9am", "tomorrow 3pm"

All times are interpreted as UTC and returned in human-readable format: "YYYY-MM-DD HH:MM:SS UTC"

## Development

This project uses:
- Python 3.12+
- [MCP](https://modelcontextprotocol.io) FastMCP
- systemd-python for journal access
- Click for CLI interface
- dateparser for natural language datetime parsing

### Project Structure

```
journald-mcp-server/
├── journald_mcp_server/     # Main package
│   ├── __init__.py
│   ├── server.py           # MCP server implementation
│   └── datetime_utils.py   # Datetime parsing and formatting utilities
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_server.py
├── server.py              # Entry point wrapper
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
python -m pytest tests/
```
