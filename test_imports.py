#!/usr/bin/env python3
"""
Quick test script to verify all imports work correctly
"""

try:
    print("Testing imports...")
    
    # Test core imports
    from app.core.dice import DiceRoller
    from app.core.character import Character, create_character_interactive
    from app.core.session import GameSession, list_sessions
    from app.core.encounter import Encounter, create_enemy
    print("✅ Core imports successful")
    
    # Test AI imports
    from app.ai.dm import DungeonMaster
    from app.ai.prompts import PERSONALITIES, CONTENT_RATINGS
    print("✅ AI imports successful")
    
    # Test adapter imports
    from app.adapters.cli_adapter import CLIAdapter
    print("✅ Adapter imports successful")
    
    # Test CLI import
    from app.cli import run_cli
    print("✅ CLI import successful")
    
    # Test basic functionality
    dice = DiceRoller()
    result = dice.d20()
    print(f"✅ Dice roll test: {result['total']}")
    
    sessions = list_sessions()
    print(f"✅ Session list test: {len(sessions)} sessions found")
    
    print("\n🎉 All tests passed! The game should run correctly now.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
