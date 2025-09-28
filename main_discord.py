#!/usr/bin/env python3
"""
Discord Bot Main Entry Point
Run the Discord version of the AI Dungeon Master
"""

from app.adapters.discord_adapter import run_discord_bot

if __name__ == "__main__":
    print("🚀 Starting AI Dungeon Master Discord Bot...")
    run_discord_bot()
