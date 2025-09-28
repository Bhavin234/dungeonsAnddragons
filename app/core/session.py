"""
Game session management and persistence
Handles story memory, context, and save/load functionality
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class StoryEvent:
    """Individual story event for session history"""
    timestamp: str
    event_type: str  # "dm_response", "player_action", "dice_roll", "system", "combat"
    content: str
    metadata: Dict[str, Any]
    
    @classmethod
    def create(cls, event_type: str, content: str, metadata: Dict = None) -> 'StoryEvent':
        """Create a new story event with current timestamp"""
        return cls(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            content=content,
            metadata=metadata or {}
        )

class GameSession:
    """
    Manages persistent game sessions with story memory and context
    """
    
    def __init__(self, session_id: str, sessions_dir: str = "sessions"):
        """
        Initialize game session
        
        Args:
            session_id: Unique identifier for this session
            sessions_dir: Directory to store session files
        """
        self.session_id = session_id
        self.sessions_dir = sessions_dir
        self.session_file = os.path.join(sessions_dir, f"{session_id}.json")
        
        # Session state
        self.story_history: List[StoryEvent] = []
        self.current_location = "Starting Village"
        self.active_npcs: List[str] = []
        self.current_scene = ""
        self.session_notes: List[str] = []
        self.created_at = datetime.now().isoformat()
        self.last_saved = None
        
        # Game state tracking
        self.turn_count = 0
        self.in_combat = False
        self.current_encounter = None
        
        # Ensure sessions directory exists
        os.makedirs(sessions_dir, exist_ok=True)
    
    def add_story_event(self, event_type: str, content: str, metadata: Dict = None):
        """
        Add an event to the story history
        
        Args:
            event_type: Type of event (dm_response, player_action, etc.)
            content: Event content/description
            metadata: Additional event data
        """
        event = StoryEvent.create(event_type, content, metadata)
        self.story_history.append(event)
        self.turn_count += 1
        
        # Auto-save every few turns
        if self.turn_count % 3 == 0:
            self.save_session()
    
    def add_player_action(self, action: str, dice_result: Optional[Dict] = None):
        """Add a player action with optional dice result"""
        metadata = {}
        if dice_result:
            metadata["dice_result"] = dice_result
        
        self.add_story_event("player_action", action, metadata)
        
        if dice_result:
            dice_description = f"{dice_result.get('description', 'dice roll')}: {dice_result.get('total', 0)}"
            self.add_story_event("dice_roll", dice_description, dice_result)
    
    def add_dm_response(self, response: str, personality: str = None):
        """Add a DM response"""
        metadata = {}
        if personality:
            metadata["personality"] = personality
        
        self.add_story_event("dm_response", response, metadata)
    
    def get_context(self, last_n: int = 10) -> str:
        """
        Get recent story context for AI input
        
        Args:
            last_n: Number of recent events to include
            
        Returns:
            Formatted context string
        """
        if not self.story_history:
            return ""
        
        recent_events = self.story_history[-last_n:]
        context_lines = []
        
        # Add location and scene info
        if self.current_location:
            context_lines.append(f"Current Location: {self.current_location}")
        
        if self.current_scene:
            context_lines.append(f"Current Scene: {self.current_scene}")
        
        if self.active_npcs:
            context_lines.append(f"Active NPCs: {', '.join(self.active_npcs)}")
        
        if self.in_combat:
            context_lines.append("Status: Currently in combat")
        
        context_lines.append("")  # Blank line separator
        
        # Add recent story events
        for event in recent_events:
            if event.event_type == "dm_response":
                context_lines.append(f"DM: {event.content}")
            elif event.event_type == "player_action":
                context_lines.append(f"Player: {event.content}")
            elif event.event_type == "dice_roll":
                context_lines.append(f"Roll: {event.content}")
            elif event.event_type == "system":
                context_lines.append(f"System: {event.content}")
        
        return "\n".join(context_lines)
    
    def save_session(self):
        """Save session to JSON file"""
        session_data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_saved": datetime.now().isoformat(),
            "turn_count": self.turn_count,
            "current_location": self.current_location,
            "active_npcs": self.active_npcs,
            "current_scene": self.current_scene,
            "session_notes": self.session_notes,
            "in_combat": self.in_combat,
            "current_encounter": self.current_encounter,
            "story_history": [asdict(event) for event in self.story_history]
        }
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self.last_saved = session_data["last_saved"]
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    def load_session(self) -> bool:
        """
        Load session from JSON file
        
        Returns:
            True if loaded successfully, False if file not found
        """
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Load basic session info
            self.created_at = session_data.get("created_at", self.created_at)
            self.last_saved = session_data.get("last_saved")
            self.turn_count = session_data.get("turn_count", 0)
            self.current_location = session_data.get("current_location", "Starting Village")
            self.active_npcs = session_data.get("active_npcs", [])
            self.current_scene = session_data.get("current_scene", "")
            self.session_notes = session_data.get("session_notes", [])
            self.in_combat = session_data.get("in_combat", False)
            self.current_encounter = session_data.get("current_encounter")
            
            # Load story history
            story_data = session_data.get("story_history", [])
            self.story_history = []
            
            for event_data in story_data:
                event = StoryEvent(
                    timestamp=event_data.get("timestamp", ""),
                    event_type=event_data.get("event_type", "unknown"),
                    content=event_data.get("content", ""),
                    metadata=event_data.get("metadata", {})
                )
                self.story_history.append(event)
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def session_exists(self) -> bool:
        """Check if session file exists"""
        return os.path.exists(self.session_file)
    
    def start_combat(self, encounter_name: str):
        """Start a combat encounter"""
        self.in_combat = True
        self.current_encounter = encounter_name
        self.add_story_event("system", f"Combat started: {encounter_name}")
    
    def end_combat(self):
        """End combat encounter"""
        if self.in_combat:
            encounter_name = self.current_encounter or "Unknown encounter"
            self.in_combat = False
            self.current_encounter = None
            self.add_story_event("system", f"Combat ended: {encounter_name}")

def list_sessions(sessions_dir: str = "sessions") -> List[Dict]:
    """
    List all available sessions with metadata
    
    Args:
        sessions_dir: Directory to search for session files
        
    Returns:
        List of session info dictionaries
    """
    if not os.path.exists(sessions_dir):
        return []
    
    sessions = []
    for filename in os.listdir(sessions_dir):
        if filename.endswith('.json'):
            session_id = filename[:-5]  # Remove .json
            session_path = os.path.join(sessions_dir, filename)
            
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": session_id,
                    "created_at": data.get("created_at", "Unknown"),
                    "last_saved": data.get("last_saved", "Unknown"),
                    "turn_count": data.get("turn_count", 0),
                    "current_location": data.get("current_location", "Unknown")
                })
            except Exception:
                continue
    
    return sorted(sessions, key=lambda x: x.get("last_saved", ""), reverse=True)
