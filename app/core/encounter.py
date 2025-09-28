"""
Combat encounter system for D&D gameplay
Manages turn-based combat with multiple participants
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
from .dice import DiceRoller
from .character import Character

class CombatantType(Enum):
    PLAYER = "player"
    NPC = "npc" 
    ENEMY = "enemy"

@dataclass
class Combatant:
    """Individual participant in combat"""
    name: str
    combatant_type: CombatantType
    health: int
    max_health: int
    armor_class: int
    initiative: int = 0
    
    # Optional character reference for players
    character: Optional[Character] = None
    
    # Combat status
    is_conscious: bool = True
    conditions: List[str] = field(default_factory=list)
    
    def take_damage(self, damage: int) -> Dict:
        """Apply damage to combatant"""
        actual_damage = min(damage, self.health)
        self.health -= actual_damage
        
        if self.health <= 0:
            self.is_conscious = False
            if "unconscious" not in self.conditions:
                self.conditions.append("unconscious")
        
        return {
            "damage_taken": actual_damage,
            "current_health": self.health,
            "unconscious": not self.is_conscious
        }
    
    def heal(self, healing: int) -> Dict:
        """Heal the combatant"""
        old_health = self.health
        self.health = min(self.max_health, self.health + healing)
        actual_healing = self.health - old_health
        
        # If healed from unconscious, wake up
        if self.health > 0 and not self.is_conscious:
            self.is_conscious = True
            if "unconscious" in self.conditions:
                self.conditions.remove("unconscious")
        
        return {
            "healing_applied": actual_healing,
            "current_health": self.health
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
        """Check if combatant has condition"""
        return condition in self.conditions
    
    @classmethod
    def from_character(cls, character: Character) -> 'Combatant':
        """Create combatant from Character object"""
        return cls(
            name=character.name,
            combatant_type=CombatantType.PLAYER,
            health=character.health,
            max_health=character.max_health,
            armor_class=character.armor_class,
            character=character,
            conditions=character.conditions.copy()
        )

class Encounter:
    """
    Manages a combat encounter with initiative and turn order
    """
    
    def __init__(self, name: str):
        self.name = name
        self.combatants: List[Combatant] = []
        self.turn_order: List[Combatant] = []
        self.current_turn_index = 0
        self.round_number = 0
        self.is_active = False
        self.combat_log: List[str] = []
    
    def add_combatant(self, combatant: Combatant):
        """Add a combatant to the encounter"""
        self.combatants.append(combatant)
    
    def add_player(self, character: Character):
        """Add a player character to combat"""
        combatant = Combatant.from_character(character)
        self.add_combatant(combatant)
    
    def add_enemy(self, name: str, health: int, armor_class: int):
        """Add an enemy to combat"""
        enemy = Combatant(
            name=name,
            combatant_type=CombatantType.ENEMY,
            health=health,
            max_health=health,
            armor_class=armor_class
        )
        self.add_combatant(enemy)
    
    def add_npc(self, name: str, health: int, armor_class: int):
        """Add an NPC ally to combat"""
        npc = Combatant(
            name=name,
            combatant_type=CombatantType.NPC,
            health=health,
            max_health=health,
            armor_class=armor_class
        )
        self.add_combatant(npc)
    
    def roll_initiative(self):
        """Roll initiative for all combatants and set turn order"""
        for combatant in self.combatants:
            # Simple initiative: d20 + dex modifier (simplified to random)
            initiative_roll = DiceRoller.d20()
            combatant.initiative = initiative_roll["total"]
            self.log_action(f"{combatant.name} rolled {combatant.initiative} for initiative")
        
        # Sort by initiative (highest first)
        self.turn_order = sorted(self.combatants, key=lambda c: c.initiative, reverse=True)
        self.current_turn_index = 0
        
        initiative_order = ", ".join([f"{c.name} ({c.initiative})" for c in self.turn_order])
        self.log_action(f"Initiative order: {initiative_order}")
    
    def start_combat(self):
        """Start the combat encounter"""
        if not self.combatants:
            raise ValueError("Cannot start combat without combatants")
        
        self.roll_initiative()
        self.is_active = True
        self.round_number = 1
        self.log_action(f"Combat started: {self.name}")
    
    def get_current_combatant(self) -> Optional[Combatant]:
        """Get the combatant whose turn it is"""
        if not self.is_active or not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index]
    
    def next_turn(self):
        """Advance to the next combatant's turn"""
        if not self.is_active:
            return
        
        self.current_turn_index += 1
        
        # If we've gone through all combatants, start new round
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.log_action(f"Round {self.round_number} begins")
            
            # Remove unconscious combatants from turn order
            self.turn_order = [c for c in self.turn_order if c.is_conscious]
            
            # Check if combat should end
            if self.should_end_combat():
                self.end_combat()
                return
    
    def should_end_combat(self) -> bool:
        """Check if combat should end"""
        conscious_players = [c for c in self.combatants if c.combatant_type == CombatantType.PLAYER and c.is_conscious]
        conscious_enemies = [c for c in self.combatants if c.combatant_type == CombatantType.ENEMY and c.is_conscious]
        
        # Combat ends if all players or all enemies are unconscious
        return len(conscious_players) == 0 or len(conscious_enemies) == 0
    
    def end_combat(self):
        """End the combat encounter"""
        self.is_active = False
        
        # Determine outcome
        conscious_players = [c for c in self.combatants if c.combatant_type == CombatantType.PLAYER and c.is_conscious]
        conscious_enemies = [c for c in self.combatants if c.combatant_type == CombatantType.ENEMY and c.is_conscious]
        
        if len(conscious_players) > 0 and len(conscious_enemies) == 0:
            self.log_action("Victory! All enemies have been defeated!")
        elif len(conscious_players) == 0:
            self.log_action("Defeat! All players have fallen unconscious!")
        else:
            self.log_action("Combat ended!")
        
        # Sync character health back
        for combatant in self.combatants:
            if combatant.character:
                combatant.character.health = combatant.health
                combatant.character.conditions = combatant.conditions.copy()
    
    def attack(self, attacker: Combatant, target: Combatant, weapon_damage: str = "1d6") -> Dict:
        """
        Perform an attack between combatants
        
        Args:
            attacker: The attacking combatant
            target: The target of the attack
            weapon_damage: Damage dice (e.g., "1d8+2")
            
        Returns:
            Attack result dictionary
        """
        if not attacker.is_conscious:
            return {"error": f"{attacker.name} is unconscious and cannot attack"}
        
        if not target.is_conscious:
            return {"error": f"{target.name} is already unconscious"}
        
        # Roll attack (d20)
        attack_roll = DiceRoller.d20()
        attack_total = attack_roll["total"]
        
        # Check if attack hits
        hits = attack_total >= target.armor_class
        
        result = {
            "attacker": attacker.name,
            "target": target.name,
            "attack_roll": attack_total,
            "target_ac": target.armor_class,
            "hits": hits,
            "damage": 0
        }
        
        if hits:
            # Roll damage
            try:
                damage_roll = DiceRoller.parse_and_roll(weapon_damage)
                damage = max(1, damage_roll["total"])  # Minimum 1 damage
                
                # Apply damage
                damage_result = target.take_damage(damage)
                
                result.update({
                    "damage": damage,
                    "damage_roll": damage_roll,
                    "target_health": target.health,
                    "target_unconscious": not target.is_conscious
                })
                
                self.log_action(f"{attacker.name} hits {target.name} for {damage} damage! ({target.name}: {target.health}/{target.max_health} HP)")
                
                if not target.is_conscious:
                    self.log_action(f"{target.name} falls unconscious!")
            
            except ValueError as e:
                result["error"] = f"Invalid damage roll: {weapon_damage}"
        else:
            self.log_action(f"{attacker.name} attacks {target.name} but misses! (rolled {attack_total} vs AC {target.armor_class})")
        
        return result
    
    def cast_spell(self, caster: Combatant, spell_name: str, targets: List[Combatant], effect: Dict) -> Dict:
        """
        Cast a spell with various effects
        
        Args:
            caster: The spell caster
            spell_name: Name of the spell
            targets: List of targets
            effect: Effect dictionary with type and parameters
            
        Returns:
            Spell result dictionary
        """
        if not caster.is_conscious:
            return {"error": f"{caster.name} is unconscious and cannot cast spells"}
        
        result = {
            "caster": caster.name,
            "spell": spell_name,
            "targets": [t.name for t in targets],
            "effects": []
        }
        
        for target in targets:
            if effect.get("type") == "damage":
                damage_roll = DiceRoller.parse_and_roll(effect.get("damage", "1d6"))
                damage = damage_roll["total"]
                damage_result = target.take_damage(damage)
                
                result["effects"].append({
                    "target": target.name,
                    "type": "damage",
                    "amount": damage,
                    "target_health": target.health
                })
                
                self.log_action(f"{caster.name} casts {spell_name} on {target.name} for {damage} damage!")
                
            elif effect.get("type") == "healing":
                healing_roll = DiceRoller.parse_and_roll(effect.get("healing", "1d4"))
                healing = healing_roll["total"]
                heal_result = target.heal(healing)
                
                result["effects"].append({
                    "target": target.name,
                    "type": "healing",
                    "amount": healing,
                    "target_health": target.health
                })
                
                self.log_action(f"{caster.name} casts {spell_name} on {target.name}, healing {healing} HP!")
        
        return result
    
    def log_action(self, action: str):
        """Add an action to the combat log"""
        self.combat_log.append(f"[Round {self.round_number}] {action}")
    
    def get_combat_status(self) -> Dict:
        """Get current combat status"""
        if not self.is_active:
            return {"active": False, "name": self.name}
        
        current_combatant = self.get_current_combatant()
        
        return {
            "active": True,
            "name": self.name,
            "round": self.round_number,
            "current_turn": current_combatant.name if current_combatant else None,
            "combatants": [
                {
                    "name": c.name,
                    "type": c.combatant_type.value,
                    "health": f"{c.health}/{c.max_health}",
                    "conscious": c.is_conscious,
                    "conditions": c.conditions,
                    "initiative": c.initiative
                }
                for c in self.combatants
            ]
        }
    
    def get_combat_log(self, last_n: int = 10) -> List[str]:
        """Get recent combat log entries"""
        return self.combat_log[-last_n:]

# Predefined enemy templates
ENEMY_TEMPLATES = {
    "goblin": {"health": 7, "armor_class": 15, "damage": "1d6"},
    "orc": {"health": 15, "armor_class": 13, "damage": "1d8+3"},
    "skeleton": {"health": 13, "armor_class": 13, "damage": "1d6+2"},
    "wolf": {"health": 11, "armor_class": 13, "damage": "2d4+2"},
    "bandit": {"health": 11, "armor_class": 12, "damage": "1d6+1"},
    "ogre": {"health": 59, "armor_class": 11, "damage": "2d8+4"},
    "dragon_wyrmling": {"health": 75, "armor_class": 17, "damage": "2d10+4"}
}

def create_enemy(enemy_type: str, name: str = None) -> Combatant:
    """Create an enemy from template"""
    if enemy_type not in ENEMY_TEMPLATES:
        raise ValueError(f"Unknown enemy type: {enemy_type}")
    
    template = ENEMY_TEMPLATES[enemy_type]
    enemy_name = name or enemy_type.replace("_", " ").title()
    
    return Combatant(
        name=enemy_name,
        combatant_type=CombatantType.ENEMY,
        health=template["health"],
        max_health=template["health"],
        armor_class=template["armor_class"]
    )
