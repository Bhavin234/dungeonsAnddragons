"""
CLI Adapter - Bridge between console I/O and game engine
Handles user interface logic for command-line gameplay
"""

import os
import sys
from typing import Optional, Dict, List
from dotenv import load_dotenv

from app.ai.dm import DungeonMaster
from app.ai.prompts import PERSONALITIES, CONTENT_RATINGS
from app.core.character import Character, create_character_interactive
from app.core.dice import DiceRoller
from app.core.session import GameSession, list_sessions
from app.core.encounter import Encounter, create_enemy

# Load environment variables
load_dotenv()

class CLIAdapter:
    """
    Command-line interface adapter for the AI Dungeon Master
    """
    
    def __init__(self):
        self.character: Optional[Character] = None
        self.session: Optional[GameSession] = None
        self.dm: Optional[DungeonMaster] = None
        self.encounter: Optional[Encounter] = None
        self.dice = DiceRoller()
        self.running = True
        
        # Configuration
        self.provider = os.getenv("DEFAULT_AI_PROVIDER", "groq")
        self.content_rating = os.getenv("DEFAULT_CONTENT_RATING", "teen")
    
    def run(self):
        """Main CLI loop"""
        try:
            self.print_welcome()
            self.setup_game()
            self.game_loop()
        except KeyboardInterrupt:
            print("\n\nGame interrupted by user.")
            self.save_and_exit()
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()
            self.save_and_exit()
    
    def print_welcome(self):
        """Print welcome message and basic info"""
        print("=" * 60)
        print("🎲 AI DUNGEON MASTER 🎲")
        print("=" * 60)
        print("Welcome to your AI-powered D&D adventure!")
        print("Type 'help' for commands, 'quit' to exit safely")
        print()
        
        # Check API configuration
        provider = os.getenv("DEFAULT_AI_PROVIDER", "groq")
        print(f"📊 Configured AI Provider: {provider.upper()}")
        
        if provider == "groq" and not os.getenv("GROQ_API_KEY"):
            print("⚠️  WARNING: GROQ_API_KEY not found in environment!")
            print("   Please set GROQ_API_KEY in your .env file")
            print("   The game will use offline mode instead.")
        elif provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            print("⚠️  WARNING: OPENAI_API_KEY not found in environment!")
            print("   Please set OPENAI_API_KEY in your .env file")
            print("   The game will use offline mode instead.")
        elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️  WARNING: ANTHROPIC_API_KEY not found in environment!")
            print("   Please set ANTHROPIC_API_KEY in your .env file")
            print("   The game will use offline mode instead.")
        print()
    
    def setup_game(self):
        """Set up character, session, and DM"""
        # Character setup
        print("\n=== GAME SETUP ===")
        if self.should_load_character():
            self.load_existing_character()
        else:
            self.create_new_character()
        
        # Session setup  
        self.setup_session()
        
        # DM setup
        self.setup_dungeon_master()
        
        print(f"\n✅ Setup complete!")
        print(f"Character: {self.character.name} the {self.character.character_class}")
        print(f"Session: {self.session.session_id}")
        print(f"DM: {self.dm.get_personality_info()['name']}")
    
    def should_load_character(self) -> bool:
        """Ask if player wants to load existing character"""
        while True:
            choice = input("\nDo you want to (N)ew character or (L)oad existing? [N/l]: ").strip().lower()
            if choice in ['', 'n', 'new']:
                return False
            elif choice in ['l', 'load']:
                return True
            else:
                print("Please enter 'n' for new or 'l' for load.")
    
    def create_new_character(self):
        """Create a new character"""
        self.character = create_character_interactive()
    
    def load_existing_character(self):
        """Load existing character (simplified - just create new for now)"""
        print("Character loading not yet implemented. Creating new character...")
        self.character = create_character_interactive()
    
    def setup_session(self):
        """Set up game session"""
        # List existing sessions
        existing_sessions = list_sessions()
        if existing_sessions:
            print(f"\nFound {len(existing_sessions)} existing sessions:")
            for i, session_info in enumerate(existing_sessions[:5], 1):
                print(f"  {i}. {session_info['session_id']} (Turn {session_info['turn_count']}, {session_info['current_location']})")
        
        session_id = input("\nEnter session name (or press Enter for new): ").strip()
        if not session_id:
            session_id = f"{self.character.name.lower().replace(' ', '_')}_adventure"
        
        self.session = GameSession(session_id)
        
        # Try to load existing session
        if self.session.load_session():
            print(f"📖 Loaded existing session: {session_id}")
            print(f"   Current location: {self.session.current_location}")
            print(f"   Turn count: {self.session.turn_count}")
        else:
            print(f"📝 Starting new session: {session_id}")
    
    def setup_dungeon_master(self):
        """Set up the AI Dungeon Master"""
        print(f"\n=== CHOOSE YOUR DUNGEON MASTER ===")
        personalities = list(PERSONALITIES.items())
        
        for i, (key, data) in enumerate(personalities, 1):
            print(f"{i}. {data['name']} - {data['description']}")
        
        while True:
            try:
                choice = input(f"\nChoose your DM (1-{len(personalities)}) [1]: ").strip()
                if not choice:
                    choice = "1"
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(personalities):
                    personality_key = personalities[choice_idx][0]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(personalities)}.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Initialize DM
        try:
            self.dm = DungeonMaster(
                provider=self.provider,
                personality=personality_key,
                content_rating=self.content_rating
            )
            print(f"\n🎭 {self.dm.get_personality_info()['name']} will be your Dungeon Master!")
        except Exception as e:
            print(f"\n⚠️  Could not initialize AI provider ({e})")
            print("The game will continue with offline mode.")
            # Create DM in offline mode instead of forcing OpenAI
            self.dm = DungeonMaster(provider="offline", personality=personality_key, content_rating=self.content_rating)
    
    def game_loop(self):
        """Main game loop"""
        # Start the adventure if new session
        if self.session.turn_count == 0:
            self.start_new_adventure()
        else:
            self.show_current_status()
        
        # Main interaction loop
        while self.running:
            self.show_prompt()
            user_input = input().strip()
            
            if not user_input:
                continue
            
            self.process_command(user_input)
    
    def start_new_adventure(self):
        """Start a new adventure"""
        print(f"\n{'='*60}")
        print("🌟 BEGINNING YOUR ADVENTURE 🌟")
        print(f"{'='*60}")
        
        initial_prompt = f"Begin a new D&D adventure for {self.character.name} the {self.character.character_class} in {self.session.current_location}. Create an engaging opening scene."
        
        context = self.session.get_context(5)
        response = self.dm.generate_response(context, initial_prompt)
        
        print(f"\n🎭 {self.dm.get_personality_info()['name']}: {response}")
        self.session.add_dm_response(response, self.dm.personality)
    
    def show_current_status(self):
        """Show current game status"""
        print(f"\n{'='*60}")
        print("📖 CONTINUING YOUR ADVENTURE 📖")
        print(f"{'='*60}")
        print(f"Session: {self.session.session_id}")
        print(f"Location: {self.session.current_location}")
        print(f"Turn: {self.session.turn_count}")
        
        # Show recent context
        recent_context = self.session.get_context(3)
        if recent_context:
            print(f"\n📜 Recent Events:")
            context_lines = recent_context.split('\n')[-3:]  # Last 3 lines
            for line in context_lines:
                if line.strip():
                    print(f"   {line}")
    
    def show_prompt(self):
        """Show the game prompt"""
        health_status = f"{self.character.health}/{self.character.max_health} HP"
        location = self.session.current_location
        
        combat_indicator = " ⚔️" if self.encounter and self.encounter.is_active else ""
        
        print(f"\n[{health_status} | {location}{combat_indicator}]")
        print("What do you do? ", end="")
    
    def process_command(self, user_input: str):
        """Process user command"""
        command = user_input.lower().strip()
        
        # System commands
        if command == 'quit':
            self.save_and_exit()
            return
        elif command == 'help':
            self.show_help()
            return
        elif command == 'stats':
            self.show_character_stats()
            return
        elif command == 'inventory':
            self.show_inventory()
            return
        elif command.startswith('roll '):
            self.handle_dice_command(command)
            return
        elif command == 'combat status' and self.encounter:
            self.show_combat_status()
            return
        elif command == 'save':
            self.session.save_session()
            print("💾 Game saved!")
            return
        
        # Game actions
        self.handle_game_action(user_input)
    
    def handle_game_action(self, action: str):
        """Handle regular game action"""
        # Check if action might need a dice roll
        dice_result = None
        action_lower = action.lower()
        
        dice_keywords = [
            'attack', 'hit', 'strike', 'fight',
            'climb', 'jump', 'leap',
            'persuade', 'convince', 'charm',
            'search', 'look for', 'investigate', 'examine',
            'lockpick', 'pick lock', 'open',
            'sneak', 'stealth', 'hide',
            'cast', 'spell', 'magic'
        ]
        
        if any(keyword in action_lower for keyword in dice_keywords):
            dice_result = self.dice.d20()
            print(f"\n🎲 Rolling d20: {dice_result['total']}")
        
        # Add to session
        self.session.add_player_action(action, dice_result)
        
        # Get AI response
        context = self.session.get_context(10)
        response = self.dm.generate_response(context, action, dice_result)
        
        print(f"\n🎭 {self.dm.get_personality_info()['name']}: {response}")
        self.session.add_dm_response(response, self.dm.personality)
        
        # Update location if traveling (for offline mode)
        if any(keyword in action_lower for keyword in ['go', 'walk', 'move', 'travel', 'head', 'forward', 'continue']):
            # Extract location from response if possible
            if 'arrive at' in response or 'reached' in response:
                # Try to extract location names
                location_indicators = ['Whispering Woods', 'Crumbling Tower', 'Silverpeak River', 
                                     'Shadowmere Cave', 'Millhaven Village', 'Restwood Cemetery', 
                                     'Four Winds Crossing', 'marketplace', 'forest', 'village']
                for location in location_indicators:
                    if location in response:
                        self.session.current_location = location
                        break
        
        # Check for combat initiation or other special events
        self.check_for_special_events(response)
    
    def check_for_special_events(self, dm_response: str):
        """Check DM response for special events like combat"""
        response_lower = dm_response.lower()
        
        # Simple combat detection
        combat_keywords = ['roll initiative', 'combat begins', 'attack you', 'draws weapon', 'hostile']
        if any(keyword in response_lower for keyword in combat_keywords) and not (self.encounter and self.encounter.is_active):
            self.initiate_simple_combat()
    
    def initiate_simple_combat(self):
        """Start a simple combat encounter"""
        print("\n⚔️  COMBAT INITIATED! ⚔️")
        
        # Create encounter
        self.encounter = Encounter("Random Encounter")
        self.encounter.add_player(self.character)
        
        # Add a simple enemy
        enemy = create_enemy("goblin", "Hostile Goblin")
        self.encounter.add_combatant(enemy)
        
        # Start combat
        self.encounter.start_combat()
        self.session.start_combat("Random Encounter")
        
        print("🎲 Initiative rolled!")
        print(f"Turn order: {', '.join([c.name for c in self.encounter.turn_order])}")
    
    def show_combat_status(self):
        """Show current combat status"""
        if not self.encounter or not self.encounter.is_active:
            print("Not currently in combat.")
            return
        
        status = self.encounter.get_combat_status()
        print(f"\n⚔️  COMBAT STATUS - {status['name']} ⚔️")
        print(f"Round: {status['round']}")
        print(f"Current Turn: {status['current_turn']}")
        print("\nCombatants:")
        
        for combatant in status['combatants']:
            status_icon = "💀" if not combatant['conscious'] else "⚡" if combatant['name'] == status['current_turn'] else "🛡️"
            conditions_str = f" [{', '.join(combatant['conditions'])}]" if combatant['conditions'] else ""
            print(f"  {status_icon} {combatant['name']}: {combatant['health']}{conditions_str}")
    
    def handle_dice_command(self, command: str):
        """Handle manual dice rolling"""
        try:
            # Parse roll command (e.g., "roll 1d20+3")
            dice_str = command[5:].strip()  # Remove "roll "
            result = self.dice.parse_and_roll(dice_str)
            
            rolls_display = f"[{', '.join(map(str, result['rolls']))}]" if len(result['rolls']) > 1 else str(result['rolls'][0])
            modifier_display = f" + {result['modifier']}" if result['modifier'] > 0 else f" - {abs(result['modifier'])}" if result['modifier'] < 0 else ""
            
            print(f"🎲 {result['description']}: {rolls_display}{modifier_display} = {result['total']}")
            
        except ValueError as e:
            print(f"❌ Invalid dice format: {e}")
            print("Examples: 'roll 1d20', 'roll 2d6+3', 'roll 1d8-1'")
    
    def show_help(self):
        """Display help information"""
        print(f"\n{'='*60}")
        print("📋 AVAILABLE COMMANDS")
        print(f"{'='*60}")
        print("BASIC ACTIONS:")
        print("  Just type what you want to do! Examples:")
        print("  • 'search the room'")
        print("  • 'talk to the innkeeper'") 
        print("  • 'attack the goblin'")
        print("  • 'cast fireball'")
        print()
        print("DICE COMMANDS:")
        print("  roll XdY+Z    - Roll dice (e.g., 'roll 1d20+3', 'roll 2d6')")
        print()
        print("CHARACTER COMMANDS:")
        print("  stats         - Show character statistics")
        print("  inventory     - Show your items and equipment")
        print()
        print("GAME COMMANDS:")
        print("  combat status - Show combat information (if in combat)")
        print("  save          - Save game session")
        print("  help          - Show this help")
        print("  quit          - Save and exit game")
        print()
        print("💡 TIP: Actions like 'attack', 'climb', 'persuade' automatically trigger dice rolls!")
    
    def show_character_stats(self):
        """Display character information"""
        print(f"\n{'='*50}")
        print(f"📊 {self.character.name.upper()} THE {self.character.character_class.upper()}")
        print(f"{'='*50}")
        print(f"Level: {self.character.level} | Experience: {self.character.experience} XP")
        print(f"Health: {self.character.health}/{self.character.max_health} HP")
        print(f"Armor Class: {self.character.armor_class}")
        print(f"Gold: {self.character.gold}")
        print()
        print("ABILITY SCORES:")
        abilities = [
            ("Strength", self.character.strength),
            ("Dexterity", self.character.dexterity), 
            ("Constitution", self.character.constitution),
            ("Intelligence", self.character.intelligence),
            ("Wisdom", self.character.wisdom),
            ("Charisma", self.character.charisma)
        ]
        
        for ability, score in abilities:
            modifier = self.character.get_modifier(ability.lower())
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            print(f"  {ability:12}: {score:2d} ({mod_str})")
        
        if self.character.conditions:
            print(f"\nCONDITIONS: {', '.join(self.character.conditions)}")
        
        print(f"\nSTATUS: {self.character.get_status_summary()}")
    
    def show_inventory(self):
        """Display character inventory"""
        print(f"\n{'='*40}")
        print(f"🎒 {self.character.name.upper()}'S INVENTORY")
        print(f"{'='*40}")
        print(f"Gold: {self.character.gold} gp")
        print()
        
        if self.character.inventory:
            print("ITEMS:")
            for i, item in enumerate(self.character.inventory, 1):
                print(f"  {i:2d}. {item}")
        else:
            print("Your inventory is empty.")
        
        if self.character.temporary_hp > 0:
            print(f"\nTemporary HP: {self.character.temporary_hp}")
    
    def save_and_exit(self):
        """Save the game and exit"""
        if self.session:
            print("\n💾 Saving your adventure...")
            if self.session.save_session():
                print(f"✅ Session saved: {self.session.session_id}")
            else:
                print("❌ Failed to save session")
        
        print("\n🎲 Thank you for playing! Your adventure awaits your return!")
        print("   Farewell, brave adventurer!")
        self.running = False
        sys.exit(0)
