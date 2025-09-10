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

class LoginAutomationAgent:
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
            name="Login Automation Assistant",
            instructions="""You are a specialized assistant for web login automation using Playwright. 
            
            When performing login actions, follow these steps:
            1. Navigate to the login page
            2. Take a screenshot of the login page
            3. Look for login form elements:
               - Email/username input fields (type='email', type='text', name/placeholder containing 'email', 'username', 'user')
               - Password input fields (type='password')
               - Submit buttons (text like 'Login', 'Sign In', 'Submit', or type='submit')
            4. Fill in the login form with the provided credentials
            5. Take a screenshot after filling the form
            6. Submit the form
            7. Take a screenshot after login attempt
            8. Check if login was successful by looking for success indicators or error messages
            
            Always save screenshots with descriptive names like:
            - 'login_page.png'
            - 'login_form_filled.png' 
            - 'login_result.png'
            - 'dashboard_after_login.png'
            
            Be thorough and report any errors or issues encountered during the login process.""",
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
        """Generate a PDF report of the login session"""
        report_filename = f"{self.reports_dir}/login_automation_{self.session_id}.pdf"
        
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
        story.append(Paragraph("Login Automation Report", title_style))
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
        story.append(Paragraph("Login Automation Log", styles['Heading2']))
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
            story.append(Paragraph(f"<b>Step {i}:</b> {log_entry['action']}", action_style))
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

    async def run_login_automation(self, url, username=None, password=None):
        """Run a complete login automation workflow"""
        try:
            # Start the Playwright MCP server
            async with MCPServerStdio(
                name="Playwright MCP server",
                params={
                    "command": "npx",
                    "args": [
                        "-y", 
                        "@playwright/mcp@latest", 
                        "--output-dir", self.output_dir,
                        "--timeout-action", "30000",
                        "--timeout-navigation", "60000",
                        "--isolated",
                        "--headless"
                    ],
                },
                client_session_timeout_seconds=60.0,
                cache_tools_list=True,
            ) as server:
                logger.info("MCP server started successfully")
                self.log_action("MCP Server Started", "Server initialized successfully")
                
                # Create and initialize the AI agent
                agent = await self.create_mcp_ai_agent(server)
                logger.info("AI agent created successfully")
                self.log_action("AI Agent Created", "Agent initialized successfully")

                # Build the login command
                login_command = f"Navigate to {url} and take a screenshot of the login page"
                
                if username and password:
                    login_command += f". Then perform a login with username '{username}' and password '{password}'. Take screenshots at each step: before filling the form, after filling the form, and after submitting. Check if the login was successful."
                else:
                    login_command += ". Look for login form elements and take screenshots of the login page."

                print(f"\n🚀 Starting Login Automation for: {url}")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📊 Session ID: {self.session_id}")
                print("-" * 60)

                # Execute the login automation
                logger.info(f"Executing login command: {login_command}")
                self.log_action(f"Login Automation Started", f"URL: {url}")
                
                output = await asyncio.wait_for(
                    Runner.run(agent, input=login_command),
                    timeout=180.0  # 3 minute timeout for login automation
                )

                # Log the result
                result_text = output.final_output[:500] + "..." if len(output.final_output) > 500 else output.final_output
                self.log_action("Login Automation Completed", result_text)

                print(f"\n✅ Login Automation Completed!")
                print(f"📋 Result: {output.final_output}")
                
                return output.final_output
                        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Login automation failed: {e}")
            print(f"❌ Login automation failed: {e}")
            self.log_action("Login Automation Error", error=error_msg)
            return None
        
        finally:
            # Generate final report
            print("\n📊 Generating PDF report...")
            self.collect_screenshots()
            report_file = self.generate_pdf_report()
            print(f"✅ PDF report generated: {report_file}")

async def main():
    print("🔐 Login Automation Agent")
    print("=" * 50)
    
    # Get user input
    url = input("Enter the login URL (e.g., http://localhost:81/dashboard/): ").strip()
    if not url:
        url = "http://localhost:81/dashboard/"
        print(f"Using default URL: {url}")
    
    username = input("Enter username (optional, press Enter to skip): ").strip()
    password = input("Enter password (optional, press Enter to skip): ").strip()
    
    # Create and run the automation
    agent = LoginAutomationAgent()
    result = await agent.run_login_automation(url, username if username else None, password if password else None)
    
    if result:
        print("\n🎉 Login automation completed successfully!")
    else:
        print("\n❌ Login automation failed. Check the logs and PDF report for details.")

if __name__ == "__main__":
    asyncio.run(main())
