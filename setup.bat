@echo off
echo Setting up Indico MCP Server on Windows...

REM Create virtual environment
python -m venv .venv

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

REM Copy example files
if not exist .env copy .env.example .env
if not exist server_config.json copy server_config.windows.example.json server_config.json

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your INDICO_TOKEN (and optionally other config)
echo 2. Run the server: .venv\Scripts\python.exe server.py
echo 3. Or test with inspector: npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server.py
echo 4. Legacy single-file version still available: .venv\Scripts\python.exe indico_mcp.py
