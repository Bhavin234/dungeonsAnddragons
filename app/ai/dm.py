"""
Provider-agnostic Dungeon Master AI wrapper
Handles communication with different LLM providers
"""

import os
from typing import Dict, Optional
from .prompts import get_system_prompt, get_fallback_response

class DungeonMaster:
    """
    Provider-agnostic AI Dungeon Master
    
    Supports multiple AI providers with consistent interface
    """
    
    def __init__(self, provider: str = "groq", personality: str = "serious", content_rating: str = "teen"):
        """
        Initialize the Dungeon Master
        
        Args:
            provider: AI provider ("groq", "openai", "anthropic", "offline")
            personality: DM personality from prompts.PERSONALITIES
            content_rating: Content rating from prompts.CONTENT_RATINGS
        """
        self.provider = provider.lower()
        self.personality = personality
        self.content_rating = content_rating
        self.system_prompt = get_system_prompt(personality, content_rating)
        
        # Initialize provider-specific clients
        self._client = None
        
        # Check for offline mode first
        if self.provider == "offline" or not self._has_api_key():
            print("🤖 Running in OFFLINE mode - using pre-written responses")
            self.provider = "offline"
        else:
            self._init_provider()
    
    def _has_api_key(self) -> bool:
        """Check if we have valid API keys"""
        return bool(os.getenv("GROQ_API_KEY")) or bool(os.getenv("OPENAI_API_KEY")) or bool(os.getenv("ANTHROPIC_API_KEY"))
    
    def _init_provider(self):
        """Initialize the AI provider client"""
        if self.provider == "groq":
            self._init_groq()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "offline":
            pass  # No initialization needed for offline mode
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _init_groq(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self._client = Groq(api_key=api_key)
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self._client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic client"""
        # TODO: Implement Anthropic/Claude integration
        # try:
        #     import anthropic
        #     api_key = os.getenv("ANTHROPIC_API_KEY")
        #     if not api_key:
        #         raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        #     self._client = anthropic.Anthropic(api_key=api_key)
        # except ImportError:
        #     raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        raise NotImplementedError("Anthropic provider not yet implemented. Coming soon!")
    
    def generate_response(self, context: str, player_action: str, dice: Optional[Dict] = None) -> str:
        """
        Generate DM response to player action
        
        Args:
            context: Recent story context and game state
            player_action: The player's current action/input
            dice: Optional dice roll result dict with 'description' and 'total'
            
        Returns:
            DM response string
        """
        try:
            return self._call_ai(context, player_action, dice)
        except Exception as e:
            print(f"AI call failed: {e}")
            return get_fallback_response(self.personality)
    
    def _call_ai(self, context: str, player_action: str, dice: Optional[Dict] = None) -> str:
        """Call the AI provider with the formatted prompt"""
        
        # Build the user prompt
        user_prompt = f"Player action: {player_action}"
        
        if context:
            user_prompt = f"Recent story context:\n{context}\n\n{user_prompt}"
        
        if dice:
            user_prompt += f"\n\nDice roll result: {dice.get('description', '')} = {dice.get('total', 0)}"
        
        if self.provider == "groq":
            return self._call_groq(user_prompt)
        elif self.provider == "openai":
            return self._call_openai(user_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(user_prompt)
        elif self.provider == "offline":
            return self._call_offline(player_action, dice)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _call_groq(self, user_prompt: str) -> str:
        """Make Groq API call"""
        response = self._client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated to current available model
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_openai(self, user_prompt: str) -> str:
        """Make OpenAI API call"""
        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper than GPT-4
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,  # Reduced from 500 to save costs
            temperature=0.7  # Slightly reduced for more focused responses
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_anthropic(self, user_prompt: str) -> str:
        """Make Anthropic API call"""
        # TODO: Implement when Anthropic support is added
        raise NotImplementedError("Anthropic provider not yet implemented")
    
    def _call_offline(self, player_action: str, dice: Optional[Dict] = None) -> str:
        """Generate offline responses based on keywords"""
        import random
        
        action_lower = player_action.lower()
        
        # Track if we should update location
        should_update_location = False
        new_location = None
        
        # Personality-based response prefixes
        prefixes = {
            "serious": [
                "You proceed with determination.",
                "Your actions have consequences.",
                "The path ahead requires careful consideration.",
                "You steel yourself for what lies ahead.",
                "With purpose in your stride, you continue."
            ],
            "comedic": [
                "Well, this should be interesting!",
                "*chuckles* That's one way to do it!",
                "The universe has a sense of humor today.",
                "Oh, what could possibly go wrong?",
                "*dramatic flourish* And so our hero ventures forth!"
            ],
            "mysterious": [
                "The shadows whisper of your choice...",
                "Something stirs in the darkness...",
                "The veil between worlds grows thin...",
                "Ancient forces take notice of your actions...",
                "A chill runs down your spine as you proceed..."
            ],
            "chaotic": [
                "Chaos erupts around you!",
                "The unexpected happens!",
                "Reality bends to your whim!",
                "*rolls dice behind screen* Interesting...",
                "The winds of change blow wildly!"
            ]
        }
        
        # More diverse action-based responses with story progression
        if any(word in action_lower for word in ['search', 'look', 'examine', 'investigate', 'see']):
            discoveries = [
                "You find ancient runes carved into a nearby stone.",
                "A glint of metal catches your eye - an old key half-buried in the dirt.",
                "Strange tracks lead away from this spot, heading north.",
                "You discover a hidden cache containing 20 gold pieces!",
                "Nothing immediately obvious, but you sense you're being watched.",
                "A torn piece of cloth hangs from a branch - someone passed this way recently.",
                "You spot a concealed trapdoor beneath some fallen leaves."
            ]
            outcomes = discoveries
        elif any(word in action_lower for word in ['attack', 'fight', 'strike', 'hit']):
            if dice and dice.get('total', 10) >= 15:
                outcomes = [
                    "Your attack strikes true! The goblin staggers back, clutching its wound.",
                    "A critical hit! Your blade finds the gap in its armor perfectly.",
                    "Your strike is devastating! The bandit drops his weapon in shock.",
                    "Excellent form! Your enemy is clearly outmatched."
                ]
            else:
                outcomes = [
                    "Your attack misses as the creature ducks at the last second.",
                    "The enemy's shield deflects your strike with a loud clang.",
                    "You stumble slightly, giving your foe an opening.",
                    "Your weapon glances off their thick hide harmlessly."
                ]
        elif any(word in action_lower for word in ['talk', 'speak', 'say', 'tell', 'ask']):
            social_outcomes = [
                "The merchant's eyes light up with interest at your words.",
                "The guard nods slowly, considering your request carefully.",
                "'Interesting,' the stranger murmurs, 'I may have information you seek.'",
                "The innkeeper leans in closer, lowering her voice conspiratorially.",
                "Your words seem to have the desired effect - they appear more trusting now.",
                "The old wizard strokes his beard thoughtfully at your question."
            ]
            outcomes = social_outcomes
        elif any(word in action_lower for word in ['go', 'walk', 'move', 'travel', 'head', 'forward', 'continue']):
            # Generate new locations and scenarios
            locations = [
                ('a dense forest', 'Whispering Woods', 'Ancient trees tower overhead, their branches blocking most sunlight.'),
                ('an abandoned watchtower', 'Crumbling Tower', 'The stone structure looks like it once guarded this road.'),
                ('a rushing river', 'Silverpeak River', 'Clear water flows swiftly over smooth stones.'),
                ('a mysterious cave entrance', 'Shadowmere Cave', 'Cool air flows from the dark opening.'),
                ('a small village', 'Millhaven Village', 'Smoke rises from several chimneys in the distance.'),
                ('an ancient graveyard', 'Restwood Cemetery', 'Weathered headstones dot the hillside.'),
                ('a crossroads with a signpost', 'Four Winds Crossing', 'Multiple paths diverge here, each leading to different destinations.')
            ]
            location_desc, location_name, detail = random.choice(locations)
            outcomes = [
                f"After traveling for some time, you arrive at {location_desc}. {detail} You have reached {location_name}.",
                f"Your journey leads you to {location_desc}. {detail} The locals call this place {location_name}.",
                f"The path winds through changing terrain until you find yourself at {location_desc}. {detail}"
            ]
        elif any(word in action_lower for word in ['rest', 'sleep', 'camp']):
            rest_outcomes = [
                "You find a safe spot to rest. After a few hours, you feel refreshed and ready to continue. (+5 HP)",
                "Your rest is interrupted by strange sounds in the night, but nothing attacks.",
                "You sleep peacefully under the stars and wake feeling invigorated.",
                "During your rest, you have a strange dream about a hooded figure..."
            ]
            outcomes = rest_outcomes
        elif any(word in action_lower for word in ['cast', 'spell', 'magic']):
            magic_outcomes = [
                "Your spell crackles with energy as arcane forces bend to your will!",
                "The magical energy flows through you, illuminating the area briefly.",
                "Your incantation echoes strangely, as if the very air is listening.",
                "Sparks of mystical energy dance around your fingertips."
            ]
            outcomes = magic_outcomes
        elif any(word in action_lower for word in ['climb', 'jump', 'leap']):
            athletic_outcomes = [
                "Your athletic training serves you well as you navigate the obstacle.",
                "With effort and determination, you manage the challenging maneuver.",
                "Your attempt is partially successful, though not without difficulty.",
                "You complete the physical challenge, breathing heavily from the exertion."
            ]
            outcomes = athletic_outcomes
        else:
            # More varied generic responses with story hooks
            generic_outcomes = [
                "Your action catches the attention of a nearby NPC who approaches curiously.",
                "As you act, you notice something interesting about your surroundings.",
                "Your decision leads to an unexpected development in your adventure.",
                "The world around you seems to shift slightly in response to your choice.",
                "A new opportunity presents itself as a result of your actions.",
                "You sense that your actions may have consequences later in your journey."
            ]
            outcomes = generic_outcomes
        
        # Build response with more personality
        prefix = random.choice(prefixes.get(self.personality, prefixes['serious']))
        outcome = random.choice(outcomes)
        
        # Add dice result flavor
        dice_text = ""
        if dice:
            roll_total = dice.get('total', 10)
            if roll_total >= 18:
                dice_text = " Your exceptional effort shows remarkable results!"
            elif roll_total >= 15:
                dice_text = " Your efforts prove quite successful!"
            elif roll_total >= 10:
                dice_text = " Things go reasonably well."
            elif roll_total <= 5:
                dice_text = " Unfortunately, things don't go as planned."
            else:
                dice_text = " The results are mixed."
        
        # Add occasional story hooks
        story_hooks = [
            "",  # Most of the time, no hook
            "",
            "",
            "\n\nIn the distance, you hear the sound of approaching hoofbeats.",
            "\n\nA mysterious figure watches you from the shadows before disappearing.",
            "\n\nYou find a hastily scrawled note that reads: 'Beware the full moon.'",
            "\n\nA merchant caravan approaches, their guards looking wary.",
            "\n\nStorm clouds are gathering on the horizon."
        ]
        
        story_hook = random.choice(story_hooks)
        
        return f"{prefix} {outcome}{dice_text}{story_hook}\n\nWhat do you do next?"
    
    def get_personality_info(self) -> Dict:
        """Get information about current personality"""
        from .prompts import PERSONALITIES
        return PERSONALITIES.get(self.personality, PERSONALITIES["serious"])
