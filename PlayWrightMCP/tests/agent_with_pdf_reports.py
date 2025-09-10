import asyncio
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import glob
from agents import (
    Runner,
    Agent,
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_tracing_disabled
)
from openai import AsyncOpenAI
from agents.mcp import MCPServerStdio

# Load environment variables from the .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read the required secrets envs from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class PlaywrightAgent:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = "output"
        self.screenshots_dir = f"{self.output_dir}/screenshots"
        self.reports_dir = f"{self.output_dir}/reports"
        self.session_screenshots = []
        self.session_log = []
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    async def create_mcp_ai_agent(self, mcp_server):
        # Initialize Gemini client using its OpenAI-compatible interface
        gemini_client = AsyncOpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        # Set the default OpenAI client to Gemini
        set_default_openai_client(gemini_client)
        # Disable tracing to avoid tracing errors being logged in the terminal
        set_tracing_disabled(True)

        # Create an agent configured to use the MCP server and Gemini model
        agent = Agent(
            name="Playwright Assistant",
            instructions="""You are a helpful assistant that can control web browsers using Playwright. 
            When asked to navigate to websites, take screenshots, or perform login actions, use the available browser tools.
            Always be specific about the actions you take. For login actions, look for common login form elements like:
            - Input fields with type='email', type='text', or name/placeholder containing 'email', 'username', 'user'
            - Password fields with type='password'
            - Submit buttons with text like 'Login', 'Sign In', 'Submit', or type='submit'
            - Look for forms and fill them appropriately.
            When taking screenshots, save them with descriptive names.""",
            model=OpenAIChatCompletionsModel(
                model="gemini-2.0-flash",
                openai_client=gemini_client,
            ),
            mcp_servers=[mcp_server]
        )

        return agent

    def log_action(self, action, result=None, error=None):
        """Log an action for the session"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "result": result,
            "error": error
        }
        self.session_log.append(log_entry)
        logger.info(f"[{timestamp}] {action}")

    def collect_screenshots(self):
        """Collect all screenshots from the current session"""
        # Look for screenshots in the current directory and output directory
        screenshot_patterns = [
            "*.png",
            f"{self.output_dir}/*.png",
            f"{self.screenshots_dir}/*.png"
        ]
        
        for pattern in screenshot_patterns:
            files = glob.glob(pattern)
            for file in files:
                if file not in self.session_screenshots:
                    self.session_screenshots.append(file)

    def generate_pdf_report(self):
        """Generate a PDF report of the session"""
        report_filename = f"{self.reports_dir}/playwright_session_{self.session_id}.pdf"
        
        doc = SimpleDocTemplate(report_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("Playwright Automation Report", title_style))
        story.append(Spacer(1, 12))
        
        # Session Info
        info_style = ParagraphStyle(
            'SessionInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        story.append(Paragraph(f"<b>Session ID:</b> {self.session_id}", info_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"<b>Total Actions:</b> {len(self.session_log)}", info_style))
        story.append(Spacer(1, 20))
        
        # Actions Log
        story.append(Paragraph("Actions Log", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        for i, log_entry in enumerate(self.session_log, 1):
            # Action header
            action_style = ParagraphStyle(
                'ActionHeader',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=6,
                textColor=colors.darkblue
            )
            story.append(Paragraph(f"<b>Action {i}:</b> {log_entry['action']}", action_style))
            story.append(Paragraph(f"<b>Time:</b> {log_entry['timestamp']}", styles['Normal']))
            
            if log_entry.get('result'):
                story.append(Paragraph(f"<b>Result:</b> {log_entry['result']}", styles['Normal']))
            
            if log_entry.get('error'):
                error_style = ParagraphStyle(
                    'Error',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.red
                )
                story.append(Paragraph(f"<b>Error:</b> {log_entry['error']}", error_style))
            
            story.append(Spacer(1, 12))
        
        # Screenshots Section
        if self.session_screenshots:
            story.append(PageBreak())
            story.append(Paragraph("Screenshots", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            for screenshot in self.session_screenshots:
                if os.path.exists(screenshot):
                    try:
                        # Add screenshot with caption
                        img = Image(screenshot, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Paragraph(f"<i>{os.path.basename(screenshot)}</i>", styles['Caption']))
                        story.append(Spacer(1, 12))
                    except Exception as e:
                        story.append(Paragraph(f"<b>Error loading screenshot:</b> {screenshot} - {str(e)}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {report_filename}")
        return report_filename

    async def run(self):
        try:
            # Start the Playwright MCP server with better configuration
            async with MCPServerStdio(
                name="Playwright MCP server",
                params={
                    "command": "npx",
                    "args": [
                        "-y", 
                        "@playwright/mcp@latest", 
                        "--output-dir", self.output_dir,
                        "--timeout-action", "30000",  # 30 second action timeout
                        "--timeout-navigation", "60000",  # 60 second navigation timeout
                        "--isolated",  # Keep browser profile in memory, avoid conflicts
                        "--headless"  # Run in headless mode
                    ],
                },
                client_session_timeout_seconds=60.0,  # Increase client timeout to 60 seconds
                cache_tools_list=True,  # Cache tools list for better performance
            ) as server:
                logger.info("MCP server started successfully")
                self.log_action("MCP Server Started", "Server initialized successfully")
                
                # Create and initialize the AI agent with the running MCP server
                agent = await self.create_mcp_ai_agent(server)
                logger.info("AI agent created successfully")
                self.log_action("AI Agent Created", "Agent initialized successfully")

                print(f"\n🚀 Playwright Agent with PDF Reports Started!")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📊 Session ID: {self.session_id}")
                print(f"💡 Type 'exit' to quit and generate PDF report")
                print(f"💡 Type 'report' to generate PDF report now")
                print("-" * 60)

                # Main REPL loop to process user requests
                while True:
                    try:
                        # Read the user's request
                        request = input("\nYour request -> ")

                        # Exit condition
                        if request.lower() == "exit":
                            print("Exiting the agent...")
                            break
                        
                        # Generate report command
                        if request.lower() == "report":
                            self.collect_screenshots()
                            report_file = self.generate_pdf_report()
                            print(f"📊 PDF report generated: {report_file}")
                            continue

                        # Run the request through the agent with timeout
                        logger.info(f"Processing request: {request}")
                        self.log_action(f"User Request: {request}")
                        
                        output = await asyncio.wait_for(
                            Runner.run(agent, input=request),
                            timeout=120.0  # 2 minute timeout
                        )

                        # Log the result
                        result_text = output.final_output[:200] + "..." if len(output.final_output) > 200 else output.final_output
                        self.log_action("Request Completed", result_text)

                        # Print the result to the user
                        print(f"\n✅ Output -> \n{output.final_output}\n")
                        
                    except asyncio.TimeoutError:
                        error_msg = "Request timed out after 2 minutes"
                        print(f"⏰ {error_msg}. Please try again with a simpler request.")
                        self.log_action("Request Timeout", error=error_msg)
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error processing request: {e}")
                        print(f"❌ Error: {e}")
                        print("Please try again or use 'exit' to quit.")
                        self.log_action("Request Error", error=error_msg)
                        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to start MCP server: {e}")
            print(f"❌ Failed to start MCP server: {e}")
            print("Make sure Playwright is properly installed and configured.")
            self.log_action("MCP Server Error", error=error_msg)
        
        finally:
            # Generate final report
            print("\n📊 Generating final PDF report...")
            self.collect_screenshots()
            report_file = self.generate_pdf_report()
            print(f"✅ Final PDF report generated: {report_file}")

async def main():
    agent = PlaywrightAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
