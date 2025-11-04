#!/bin/bash
echo "Setting up Indico MCP Server on Linux/macOS..."

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install fastmcp requests python-dotenv

# Copy example files
[ ! -f .env ] && cp .env.example .env
[ ! -f server_config.json ] && cp server_config.example.json server_config.json

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your INDICO_TOKEN"
echo "2. Run the server: python indico_mcp.py"
echo "3. Or test with inspector: npx @modelcontextprotocol/inspector .venv/bin/python indico_mcp.py"
