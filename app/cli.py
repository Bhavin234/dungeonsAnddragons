"""
AI Dungeon Master CLI Module
Main entry point for command-line interface
"""

from app.adapters.cli_adapter import CLIAdapter

def run_cli():
    """Main CLI entry point"""
    adapter = CLIAdapter()
    adapter.run()
