# Playwright MCP Agent with PDF Reports

This project provides automated web testing capabilities using Playwright MCP (Model Context Protocol) with AI assistance and PDF report generation.

## Features

- AI-powered web automation using Gemini
- Automatic PDF report generation
- Screenshot capture at each step
- Organized output with screenshots and reports
- Configurable timeouts and error handling

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Gemini API key in `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

3. Install Playwright browsers:
```bash
npx playwright install
```

## Usage

### 1. General Purpose Agent with PDF Reports

```bash
python agent_with_pdf_reports.py
```

This starts an interactive agent where you can:
- Type commands like "go to http://localhost:81/dashboard/ and take a screenshot"
- Type `report` to generate a PDF report at any time
- Type `exit` to quit and generate a final PDF report

### 2. Run agent in non-headless mode

```bash
python agent_headed.py
```

### 3. Run the agent in headless mode

```bash
python agent.py
```

## Output Structure

```
output/
├── screenshots/          # All captured screenshots
├── reports/             # Generated PDF reports
└── traces/              # Playwright traces (if enabled)
```

## PDF Report Features

The generated PDF reports include:
- Session information and timestamp
- Complete action log with timestamps
- All captured screenshots with captions
- Error logs and debugging information
- Professional formatting with headers and styling

## Example Commands

### Basic Navigation and Screenshots
```
go to http://localhost:81/dashboard/ and take a screenshot
```

### Login Automation
```
Navigate to http://localhost:81/dashboard/ and perform a login with username 'admin' and password 'admin'. Take screenshots at each step.
```

### Form Filling
```
Go to http://example.com/contact and fill out the contact form with name 'John Doe', email 'john@example.com', and message 'Hello World'
```

### Complex Workflows
```
Navigate to http://localhost:81/dashboard/, take a screenshot, then look for a login form and fill it with username 'admin' and password 'admin', submit the form, and take another screenshot of the result.
```

## Troubleshooting

### Timeout Issues
If you encounter timeout errors:
1. Make sure no other Playwright processes are running: `pkill -f playwright`
2. Check that Playwright browsers are installed: `npx playwright install`
3. Try increasing timeouts in the script if needed

### Browser Issues
- The agent runs in headless mode by default
- Use `--headless` flag removal in the script for visible browser
- Check the `--isolated` flag to prevent browser conflicts

### PDF Generation Issues
- Ensure `reportlab` is installed: `pip install reportlab`
- Check that the `output/reports/` directory exists and is writable

## Configuration

You can modify the following in the scripts:
- Timeout values (currently 30s action, 60s navigation)
- Output directories
- Browser settings (headless/headed mode)
- PDF report styling and content

## Files

- `agent_with_pdf_reports.py` - General purpose agent with PDF reports
- `agent_isolated.py` - Basic agent with isolation
- `agent_headed_final.py` - Agent with visible browser
- `./tests/Login/test_login.py` - Test login feature

## Requirements

- Python 3.8+
- Playwright
- OpenAI Agents
- ReportLab
- Pillow
- python-dotenv

## Installation Options

### Option 1: Full Installation (Recommended)
```bash
pip install -r requirements.txt
```

### Option 2: Minimal Installation
```bash
pip install -r requirements-minimal.txt
```

### Option 3: Manual Installation
```bash
pip install openai-agents openai-agents-mcp playwright reportlab python-dotenv
```

## Requirements Files

- **`requirements.txt`** - Complete installation with all dependencies
- **`requirements-minimal.txt`** - Essential dependencies only

## Environment Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

4. Install Playwright browsers:
```bash
npx playwright install
```
