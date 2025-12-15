# Journald MCP Server

An MCP server for accessing systemd journal logs.

## Features

- List systemd units from journal logs
- Access journal entries (TODO)

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

Run the server with:

```bash
python server.py [OPTIONS]
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

The server provides the following MCP resources:

- `journal://units`: List unique systemd units from the last 30 minutes of journal logs
- `journal://syslog-identifiers`: List unique syslog identifiers from the last 30 minutes of journal logs

## Development

This project uses:
- Python 3.12+
- [MCP](https://modelcontextprotocol.io) FastMCP
- systemd-python for journal access
- Click for CLI interface

### Project Structure

```
journald-mcp-server/
├── journald_mcp_server/     # Main package
│   ├── __init__.py
│   └── server.py           # MCP server implementation
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
