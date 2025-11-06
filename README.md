# Indico MCP Server PROTOTYPE

A Model Context Protocol (MCP) server providing access to CERN Indico public events.
https://github.com/indico/indico

## Features

- Search upcoming public events at CERN
- Get detailed event information
- Filter by date ranges, categories, and keywords
- Built-in caching for improved performance
- **Public events only** (no authentication required)

## Project Structure

```
indico-mcp/
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
│
├── src/                      # Source code package
│   ├── __init__.py
│   ├── server.py             # MCP server implementation
│   ├── client.py             # Indico API client
│   ├── config.py             # Configuration management
│   ├── models.py             # Data models and normalizers
│   └── utils.py              # Utility functions
│
├── scripts/                  # Setup and utility scripts
│   ├── setup.sh             # Linux/macOS setup script
│   └── setup.bat            # Windows setup script
│
└── config/                   # Configuration examples
    ├── server_config.example.json
    └── server_config.windows.example.json
```

## Quick Start

### 1. Setup

**Linux/macOS:**
```bash
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

### 2. Run

**Direct execution:**
```bash
python main.py
```

**With MCP Inspector (for testing):**
```bash
npx @modelcontextprotocol/inspector .venv/bin/python main.py
```

**Windows:**
```cmd
.venv\Scripts\python.exe main.py
```

## Available Tools

### 1. `search_events`
Search upcoming public CERN Indico events by keyword.

**Parameters:**
- `keyword` (str): Text to search for in event titles
- `limit` (int, optional): Maximum results (default: 10, max: 500)
- `category_id` (int, optional): Indico category ID (default: 0 = all)
- `days_ahead` (int, optional): Days to look ahead (default: 30)
- `from_date` (str, optional): Start date YYYY-MM-DD
- `to_date` (str, optional): End date YYYY-MM-DD

**Example:**
```python
search_events("machine learning", limit=5)
```

### 2. `get_event_details`
Get detailed information for a specific public Indico event.

**Parameters:**
- `event_id` (int): Numeric Indico event ID

**Example:**
```python
get_event_details(1234567)
```

### 3. `upcoming_public`
List upcoming public events at CERN.

**Parameters:**
- `days` (int, optional): Days to look ahead (default: 7)
- `limit` (int, optional): Maximum events (default: 10, max: 500)
- `category_id` (int, optional): Indico category ID (default: 0 = all)
- `from_date` (str, optional): Start date YYYY-MM-DD
- `to_date` (str, optional): End date YYYY-MM-DD

**Example:**
```python
upcoming_public(days=14, limit=20)
```

### 4. `server_status`
Get server status and configuration information.

**Example:**
```python
server_status()
```

## Configuration

### Environment Variables (Optional)

You can customize behavior by creating a `.env` file:

```bash
INDICO_BASE_URL=https://indico.cern.ch
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_SIZE=128
```

**Note: This server only accesses public events. Authentication is disabled for security purposes.**

### MCP Client Configuration

For Claude Desktop or other MCP clients, use the configuration from `config/server_config.example.json`:

```json
{
  "servers": [
    {
      "name": "indico",
      "command": "python",
      "args": ["main.py"],
      "env": {},
      "enabled": true
    }
  ]
}
```

## Development

### Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/
```

## Requirements

- Python 3.8+
- fastmcp
- requests
- python-dotenv

## License

MIT

## Support

- Report issues on GitHub
- Check CERN Indico documentation: https://indico.cern.ch/
