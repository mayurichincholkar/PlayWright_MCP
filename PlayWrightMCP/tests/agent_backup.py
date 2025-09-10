import asyncio
from dotenv import load_dotenv
import os
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
        instructions="You are a helpful assistant",
        model=OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=gemini_client,
        ),
        mcp_servers=[mcp_server]
    )

    return agent

async def run():
    # Start the Playwright MCP server via npx
    async with MCPServerStdio(
        name="Playwright MCP server",
        params={
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--output-dir", "./"],
        },
    ) as server:
        # Create and initialize the AI agent with the running MCP server
        agent = await create_mcp_ai_agent(server)

        # Main REPL loop to process user requests
        while True:
            # Read the user's request
            request = input("Your request -> ")

            # Exit condition
            if request.lower() == "exit":
                print("Exiting the agent...")
                break

            # Run the request through the agent
            output = await Runner.run(agent, input=request)

            # Print the result to the user
            print(f"Output -> \n{output.final_output}\n\n")

if __name__ == "__main__":
    asyncio.run(run())