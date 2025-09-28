"""
Character system for D&D gameplay
Manages character stats, progression, and state
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from .dice import DiceRoller
import json

@dataclass
class Character:
    """
    Player character with full D&D-style attributes
    """
    name: str
    character_class: str
    level: int = 1
    experience: int = 0
    
    # Core ability scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    # Combat stats
    health: int = 10
    max_health: int = 10
    armor_class: int = 10
    
    # Equipment and inventory
    inventory: List[str] = field(default_factory=lambda: ["Basic weapon", "Starting armor", "Adventurer's pack"])
    gold: int = 100
    
    # Status tracking
    conditions: List[str] = field(default_factory=list)
    temporary_hp: int = 0
    
    def __post_init__(self):
        """Initialize calculated values after creation"""
        if self.max_health == 10:  # Default value, calculate based on class and constitution
            self.max_health = self._calculate_starting_hp()
            self.health = self.max_health
        
        if self.armor_class == 10:  # Default value, calculate based on dexterity
            self.armor_class = 10 + self.get_modifier("dexterity")
    
    def get_modifier(self, ability: str) -> int:
        """
        Calculate ability modifier from ability score
        
        Args:
            ability: Ability name (strength, dexterity, etc.)
            
        Returns:
            Ability modifier
        """
        ability = ability.lower()
        ability_scores = {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma
        }
        
        if ability not in ability_scores:
            raise ValueError(f"Unknown ability: {ability}")
        
        return (ability_scores[ability] - 10) // 2
    
    def _calculate_starting_hp(self) -> int:
        """Calculate starting HP based on class and constitution"""
        hit_dice = {
            "fighter": 10,
            "paladin": 10,
            "ranger": 10,
            "barbarian": 12,
            "rogue": 8,
            "monk": 8,
            "bard": 8,
            "cleric": 8,
            "druid": 8,
            "warlock": 8,
            "wizard": 6,
            "sorcerer": 6
        }
        
        base_hp = hit_dice.get(self.character_class.lower(), 8)
        con_modifier = self.get_modifier("constitution")
        return max(1, base_hp + con_modifier)  # Minimum 1 HP
    
    def take_damage(self, damage: int) -> Dict:
        """
        Apply damage to character
        
        Args:
            damage: Amount of damage to take
            
        Returns:
            Dict with damage details and current status
        """
        # Apply temporary HP first
        temp_damage = min(damage, self.temporary_hp)
        self.temporary_hp -= temp_damage
        remaining_damage = damage - temp_damage
        
        # Apply remaining damage to health
        actual_damage = min(remaining_damage, self.health)
        self.health -= actual_damage
        
        return {
            "damage_taken": damage,
            "temp_hp_lost": temp_damage,
            "health_lost": actual_damage,
            "current_health": self.health,
            "unconscious": self.health <= 0
        }
    
    def heal(self, healing: int) -> Dict:
        """
        Heal the character
        
        Args:
            healing: Amount of healing
            
        Returns:
            Dict with healing details
        """
        old_health = self.health
        self.health = min(self.max_health, self.health + healing)
        actual_healing = self.health - old_health
        
        return {
            "healing_attempted": healing,
            "healing_applied": actual_healing,
            "current_health": self.health,
            "fully_healed": self.health >= self.max_health
        }
    
    def add_condition(self, condition: str):
        """Add a status condition"""
        if condition not in self.conditions:
            self.conditions.append(condition)
    
    def remove_condition(self, condition: str):
        """Remove a status condition"""
        if condition in self.conditions:
            self.conditions.remove(condition)
    
    def has_condition(self, condition: str) -> bool:
        """Check if character has a specific condition"""
        return condition in self.conditions
    
    def add_item(self, item: str):
        """Add an item to inventory"""
        self.inventory.append(item)
    
    def remove_item(self, item: str) -> bool:
        """Remove an item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def has_item(self, item: str) -> bool:
        """Check if character has a specific item"""
        return item in self.inventory
    
    def gain_experience(self, xp: int):
        """Add experience points and check for level up"""
        self.experience += xp
        
        # Simple level progression (1000 XP per level)
        new_level = 1 + (self.experience // 1000)
        
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self._level_up(old_level, new_level)
    
    def _level_up(self, old_level: int, new_level: int):
        """Handle level up mechanics"""
        levels_gained = new_level - old_level
        
        # Increase max HP (simplified: +5 per level + con modifier)
        hp_gain = levels_gained * (5 + self.get_modifier("constitution"))
        self.max_health += max(1, hp_gain)  # Minimum 1 HP per level
        self.health += hp_gain  # Full heal on level up
    
    def make_ability_check(self, ability: str, difficulty: int = 15, advantage: bool = False, disadvantage: bool = False) -> Dict:
        """
        Make an ability check
        
        Args:
            ability: Ability to check
            difficulty: DC for the check
            advantage: Roll with advantage
            disadvantage: Roll with disadvantage
            
        Returns:
            Check result with success/failure
        """
        ability_score = getattr(self, ability.lower(), 10)
        result = DiceRoller.ability_check(ability_score, advantage, disadvantage)
        
        success = result["total"] >= difficulty
        
        return {
            **result,
            "ability": ability,
            "difficulty": difficulty,
            "success": success,
            "margin": result["total"] - difficulty
        }
    
    def is_alive(self) -> bool:
        """Check if character is alive"""
        return self.health > 0
    
    def is_conscious(self) -> bool:
        """Check if character is conscious"""
        return self.health > 0 and not self.has_condition("unconscious")
    
    def get_status_summary(self) -> str:
        """Get a summary of character's current status"""
        status_parts = []
        
        # Health status
        health_percent = (self.health / self.max_health) * 100
        if health_percent <= 0:
            status_parts.append("Unconscious")
        elif health_percent <= 25:
            status_parts.append("Critically wounded")
        elif health_percent <= 50:
            status_parts.append("Badly hurt")
        elif health_percent <= 75:
            status_parts.append("Wounded")
        else:
            status_parts.append("Healthy")
        
        # Conditions
        if self.conditions:
            status_parts.append(f"Conditions: {', '.join(self.conditions)}")
        
        # Temporary HP
        if self.temporary_hp > 0:
            status_parts.append(f"Temporary HP: {self.temporary_hp}")
        
        return " | ".join(status_parts)
    
    def to_dict(self) -> Dict:
        """Convert character to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        """Create character from dictionary"""
        return cls(**data)
    
    def save_to_file(self, filepath: str):
        """Save character to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Character':
        """Load character from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

def create_character_interactive() -> Character:
    """Interactive character creation"""
    print("\n=== CHARACTER CREATION ===")
    
    # Basic info
    name = input("Enter your character's name: ").strip()
    
    # Class selection
    classes = [
        "Fighter", "Wizard", "Rogue", "Cleric", 
        "Ranger", "Paladin", "Barbarian", "Bard",
        "Druid", "Monk", "Sorcerer", "Warlock"
    ]
    
    print("\nChoose your class:")
    for i, cls in enumerate(classes, 1):
        print(f"{i:2d}. {cls}")
    
    while True:
        try:
            choice = int(input("Enter your choice: ")) - 1
            if 0 <= choice < len(classes):
                character_class = classes[choice]
                break
            else:
                print(f"Please enter a number between 1 and {len(classes)}.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Roll ability scores
    print(f"\nRolling ability scores for {name} the {character_class}...")
    
    abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    ability_scores = {}
    
    for ability in abilities:
        roll_result = DiceRoller.ability_score_roll()
        ability_scores[ability.lower()] = roll_result["total"]
        print(f"{ability}: {roll_result['total']} (rolled {roll_result['kept']}, dropped {roll_result['dropped']})")
    
    # Create character
    character = Character(
        name=name,
        character_class=character_class,
        **ability_scores
    )
    
    print(f"\nWelcome, {name} the {character_class}!")
    print(f"Starting HP: {character.health}/{character.max_health}")
    print(f"Armor Class: {character.armor_class}")
    print(f"Starting Gold: {character.gold}")
    
    return character
