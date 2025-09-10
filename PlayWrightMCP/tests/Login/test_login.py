#!/usr/bin/env python3
"""
Quick Login Automation Script
Usage: python test_login.py [URL] [USERNAME] [PASSWORD]
"""

import asyncio
import sys
from login_automation import LoginAutomationAgent

async def main():
    # Parse command line arguments
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:81/dashboard/"
    username = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"�� Quick Login Automation")
    print(f"URL: {url}")
    print(f"Username: {username if username else 'Not provided'}")
    print(f"Password: {'*' * len(password) if password else 'Not provided'}")
    print("-" * 50)
    
    # Create and run the automation
    agent = LoginAutomationAgent()
    result = await agent.run_login_automation(url, username, password)
    
    if result:
        print("\n🎉 Login automation completed successfully!")
    else:
        print("\n❌ Login automation failed. Check the logs and PDF report for details.")

if __name__ == "__main__":
    asyncio.run(main())
