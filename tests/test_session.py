"""
Tests for game session management and persistence
"""

import pytest
import os
import tempfile
import json
from app.core.session import GameSession, StoryEvent, list_sessions

class TestStoryEvent:
    """Test cases for StoryEvent class"""
    
    def test_story_event_creation(self):
        """Test creating story events"""
        event = StoryEvent.create("player_action", "I search the room")
        
        assert event.event_type == "player_action"
        assert event.content == "I search the room"
        assert event.metadata == {}
        assert event.timestamp is not None
    
    def test_story_event_with_metadata(self):
        """Test creating story events with metadata"""
        metadata = {"dice_result": {"total": 15}}
        event = StoryEvent.create("dice_roll", "1d20: 15", metadata)
        
        assert event.metadata == metadata
        assert event.metadata["dice_result"]["total"] == 15

class TestGameSession:
    """Test cases for GameSession class"""
    
    def setup_method(self):
        """Set up test with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_id = "test_session"
        self.session = GameSession(self.session_id, self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_session_initialization(self):
        """Test session initialization"""
        assert self.session.session_id == "test_session"
        assert self.session.sessions_dir == self.temp_dir
        assert self.session.current_location == "Starting Village"
        assert self.session.turn_count == 0
        assert len(self.session.story_history) == 0
        assert self.session.in_combat == False
    
    def test_add_story_event(self):
        """Test adding story events"""
        self.session.add_story_event("player_action", "I look around")
        
        assert len(self.session.story_history) == 1
        assert self.session.turn_count == 1
        
        event = self.session.story_history[0]
        assert event.event_type == "player_action"
        assert event.content == "I look around"
    
    def test_add_player_action(self):
        """Test adding player actions"""
        dice_result = {"total": 15, "description": "1d20"}
        self.session.add_player_action("I attack the goblin", dice_result)
        
        # Should create both player_action and dice_roll events
        assert len(self.session.story_history) == 2
        assert self.session.story_history[0].event_type == "player_action"
        assert self.session.story_history[1].event_type == "dice_roll"
    
    def test_add_dm_response(self):
        """Test adding DM responses"""
        self.session.add_dm_response("You find a hidden door!", "serious")
        
        assert len(self.session.story_history) == 1
        event = self.session.story_history[0]
        assert event.event_type == "dm_response"
        assert event.content == "You find a hidden door!"
        assert event.metadata["personality"] == "serious"
    
    def test_get_context_empty(self):
        """Test getting context with no history"""
        context = self.session.get_context()
        assert "Current Location: Starting Village" in context
        assert "Status: Currently in combat" not in context
    
    def test_get_context_with_history(self):
        """Test getting context with story history"""
        self.session.add_player_action("I search")
        self.session.add_dm_response("You find gold!")
        
        context = self.session.get_context(5)
        assert "Player: I search" in context
        assert "DM: You find gold!" in context
        assert "Current Location: Starting Village" in context
    
    def test_save_and_load_session(self):
        """Test session persistence"""
        # Add some data
        self.session.add_story_event("player_action", "Test action")
        self.session.current_location = "Test Location"
        self.session.turn_count = 5
        
        # Save session
        success = self.session.save_session()
        assert success == True
        assert os.path.exists(self.session.session_file)
        
        # Create new session instance and load
        new_session = GameSession(self.session_id, self.temp_dir)
        loaded = new_session.load_session()
        
        assert loaded == True
        assert new_session.current_location == "Test Location"
        assert new_session.turn_count == 5
        assert len(new_session.story_history) == 1
        assert new_session.story_history[0].content == "Test action"
    
    def test_load_nonexistent_session(self):
        """Test loading session that doesn't exist"""
        nonexistent_session = GameSession("nonexistent", self.temp_dir)
        loaded = nonexistent_session.load_session()
        
        assert loaded == False
        assert nonexistent_session.current_location == "Starting Village"  # Default
    
    def test_session_exists(self):
        """Test checking if session exists"""
        assert self.session.session_exists() == False
        
        # Save session
        self.session.save_session()
        assert self.session.session_exists() == True
    
    def test_autosave_functionality(self):
        """Test that autosave works every few turns"""
        # Add 3 events to trigger autosave (every 3 turns)
        self.session.add_story_event("player_action", "Action 1")
        assert not self.session.session_exists()  # Should not save yet
        
        self.session.add_story_event("player_action", "Action 2")  
        assert not self.session.session_exists()  # Should not save yet
        
        self.session.add_story_event("player_action", "Action 3")
        assert self.session.session_exists()  # Should autosave now
    
    def test_combat_state_management(self):
        """Test combat state tracking"""
        assert self.session.in_combat == False
        
        self.session.start_combat("Goblin Fight")
        assert self.session.in_combat == True
        assert self.session.current_encounter == "Goblin Fight"
        
        self.session.end_combat()
        assert self.session.in_combat == False
        assert self.session.current_encounter is None

class TestSessionUtilityFunctions:
    """Test utility functions for session management"""
    
    def setup_method(self):
        """Set up test with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_list_sessions_empty(self):
        """Test listing sessions when directory is empty"""
        sessions = list_sessions(self.temp_dir)
        assert len(sessions) == 0
    
    def test_list_sessions_with_data(self):
        """Test listing sessions with actual session files"""
        # Create a few test sessions
        session1 = GameSession("session1", self.temp_dir)
        session1.add_story_event("player_action", "Test")
        session1.save_session()
        
        session2 = GameSession("session2", self.temp_dir)
        session2.current_location = "Forest"
        session2.save_session()
        
        # List sessions
        sessions = list_sessions(self.temp_dir)
        assert len(sessions) == 2
        
        session_ids = [s["session_id"] for s in sessions]
        assert "session1" in session_ids
        assert "session2" in session_ids

class TestSessionDataIntegrity:
    """Test data integrity and error handling"""
    
    def setup_method(self):
        """Set up test with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_id = "integrity_test"
        self.session = GameSession(self.session_id, self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_corrupted_session_file(self):
        """Test handling of corrupted session files"""
        # Create a corrupted file
        with open(self.session.session_file, 'w') as f:
            f.write("corrupted json data")
        
        # Should not crash, should return False
        loaded = self.session.load_session()
        assert loaded == False
    
    def test_session_with_unicode_content(self):
        """Test session with unicode content"""
        unicode_content = "🎲 I cast fireball! 🔥"
        self.session.add_story_event("player_action", unicode_content)
        
        # Save and reload
        assert self.session.save_session() == True
        
        new_session = GameSession(self.session_id, self.temp_dir)
        assert new_session.load_session() == True
        assert new_session.story_history[0].content == unicode_content
    
    def test_large_session_data(self):
        """Test handling of large session data"""
        # Add many events
        for i in range(100):
            self.session.add_story_event("test_event", f"Event number {i}")
        
        # Should save successfully
        assert self.session.save_session() == True
        
        # Should load successfully
        new_session = GameSession(self.session_id, self.temp_dir)
        assert new_session.load_session() == True
        assert len(new_session.story_history) == 100

if __name__ == "__main__":
    pytest.main([__file__])
