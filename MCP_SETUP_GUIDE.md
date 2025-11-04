# MCP Server Setup and Testing Guide

Complete guide for setting up, running, and testing Model Context Protocol (MCP) servers.

## Quick Start (Automated Setup)

### Linux/macOS
```bash
./setup.sh
```

### Windows
```batch
setup.bat
```

Then edit `.env` to add your API credentials.

---

## Manual Setup

### 1. Create Your MCP Server

**Linux/macOS:**
```bash
# Create project directory
mkdir my_mcp_server && cd my_mcp_server

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install fastmcp requests python-dotenv
```

**Windows:**
```batch
# Create project directory
mkdir my_mcp_server
cd my_mcp_server

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install fastmcp requests python-dotenv
```

### 2. Environment Variables Setup

Create `.env.example`:
```bash
# API Token
API_KEY=your_token_here
```

Create `.env` (gitignored):
```bash
API_KEY=actual_token_value
```

Create `.gitignore`:
```
.venv/
.env
server_config.json
__pycache__/
*.pyc
```

### 3. Write Your Server Code

Create `server.py`:

```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastMCP("my-server")

@app.tool()
def hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    if not os.getenv("API_KEY"):
        print("Warning: API_KEY not set. Check your .env file.")
    app.run()
```

### 4. Create Server Configuration

**Linux/macOS** - `server_config.example.json`:
```json
{
  "servers": [
    {
      "name": "my-server",
      "command": ".venv/bin/python",
      "args": ["server.py"],
      "env": {},
      "enabled": true
    }
  ]
}
```

**Windows** - `server_config.windows.example.json`:
```json
{
  "servers": [
    {
      "name": "my-server",
      "command": ".venv\\Scripts\\python.exe",
      "args": ["server.py"],
      "env": {},
      "enabled": true
    }
  ]
}
```

Copy the appropriate example to `server_config.json`.

### 5. Test With MCP Inspector

**Linux/macOS:**
```bash
source .venv/bin/activate
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```

**Windows:**
```batch
.venv\Scripts\activate
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server.py
```

Opens at `http://localhost:6274` - use the URL with token shown in output.

**Inspector features:**
- View all available tools
- Test tools with different parameters
- See responses in real-time

### 6. Test API Endpoints Directly

Test your actual API with curl:

```bash
curl "https://api.example.com/endpoint?param=value" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Use in Claude Desktop

**macOS:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"],
      "env": {}
    }
  }
}
```

**Windows:**

Edit `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "C:\\absolute\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["C:\\absolute\\path\\to\\server.py"],
      "env": {}
    }
  }
}
```

Restart Claude Desktop to load the server.

### 8. Use in Claude Code

**Linux:**

Edit `~/.config/claude-code/mcp_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"],
      "env": {}
    }
  }
}
```

**Windows:**

Edit `%USERPROFILE%\.config\claude-code\mcp_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "C:\\absolute\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["C:\\absolute\\path\\to\\server.py"],
      "env": {}
    }
  }
}
```

Restart Claude Code to load the server.

---

## Summary

- **fastmcp** = framework to build MCP servers
- **python-dotenv** = load environment variables from `.env` files
- **Inspector** = web UI to test tools
- **server_config.json** = config format for running servers
- Use `.env` files for secrets (never commit them)
- Always use absolute paths in production configs

## Best Practices

1. **Never commit secrets:**
   - Add `.env` to `.gitignore`
   - Provide `.env.example` as a template

2. **Use environment variables:**
   - Load with `python-dotenv`
   - Keep tokens out of code

3. **Provide example configs:**
   - `server_config.example.json` for Linux/macOS
   - `server_config.windows.example.json` for Windows
   - Users copy and customize them

4. **Automated setup scripts:**
   - `setup.sh` for Linux/macOS
   - `setup.bat` for Windows

## Common Issues

### Inspector doesn't pass environment variables
The MCP Inspector doesn't forward environment variables from your shell. Solution:
- Use `python-dotenv` and load from `.env` file
- The script automatically loads environment variables on startup

### Tools return empty results
- Check that API tokens are in `.env` file
- Verify `.env` file is in the same directory as the script
- Verify API endpoints work with direct curl tests
- Check server logs for errors

### Connection errors
- Make sure only one inspector instance is running on the same port
- Kill existing processes: `pkill -f modelcontextprotocol/inspector` (Linux/macOS) or Task Manager (Windows)
- Try a different port if needed

### Windows path issues
- Use double backslashes in JSON: `"C:\\path\\to\\file"`
- Or use forward slashes: `"C:/path/to/file"`
- Always use absolute paths in config files
