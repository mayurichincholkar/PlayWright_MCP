import asyncio
from dotenv import load_dotenv
import os
import logging
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

async def create_mcp_ai_agent(mcp_server):
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
        name="Assistant",
        instructions="You are a helpful assistant that can control web browsers using Playwright. When asked to navigate to websites or take screenshots, use the available browser tools. Be specific about the actions you take.",
        model=OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=gemini_client,
        ),
        mcp_servers=[mcp_server]
    )

    return agent

async def run():
    try:
        # Start the Playwright MCP server with isolated mode
        async with MCPServerStdio(
            name="Playwright MCP server",
            params={
                "command": "npx",
                "args": [
                    "-y", 
                    "@playwright/mcp@latest", 
                    "--output-dir", "./",
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
            
            # Create and initialize the AI agent with the running MCP server
            agent = await create_mcp_ai_agent(server)
            logger.info("AI agent created successfully")

            # Main REPL loop to process user requests
            while True:
                try:
                    # Read the user's request
                    request = input("Your request -> ")

                    # Exit condition
                    if request.lower() == "exit":
                        print("Exiting the agent...")
                        break

                    # Run the request through the agent with timeout
                    logger.info(f"Processing request: {request}")
                    output = await asyncio.wait_for(
                        Runner.run(agent, input=request),
                        timeout=120.0  # 2 minute timeout
                    )

                    # Print the result to the user
                    print(f"Output -> \n{output.final_output}\n\n")
                    
                except asyncio.TimeoutError:
                    print("Request timed out after 2 minutes. Please try again with a simpler request.")
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    print(f"Error: {e}")
                    print("Please try again or use 'exit' to quit.")
                    
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        print(f"Failed to start MCP server: {e}")
        print("Make sure Playwright is properly installed and configured.")

if __name__ == "__main__":
    asyncio.run(run())
