"""
Dice rolling system with natural language parsing
Supports standard D&D dice notation and convenience functions
"""

import random
import re
from typing import Dict, List, Union

class DiceRoller:
    """
    Advanced dice rolling system for D&D gameplay
    """
    
    @staticmethod
    def roll(sides: int, count: int = 1, modifier: int = 0) -> Dict:
        """
        Roll dice with specified parameters
        
        Args:
            sides: Number of sides on each die
            count: Number of dice to roll
            modifier: Modifier to add to total
            
        Returns:
            Dict containing rolls, modifier, total, and description
        """
        if sides < 1 or count < 1:
            raise ValueError("Sides and count must be positive integers")
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        # Build description
        desc = f"{count}d{sides}"
        if modifier > 0:
            desc += f"+{modifier}"
        elif modifier < 0:
            desc += str(modifier)
        
        return {
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
            "description": desc,
            "sides": sides,
            "count": count
        }
    
    @staticmethod
    def d20(modifier: int = 0) -> Dict:
        """Convenience method for d20 rolls"""
        return DiceRoller.roll(20, 1, modifier)
    
    @staticmethod
    def d6(count: int = 1, modifier: int = 0) -> Dict:
        """Convenience method for d6 rolls"""
        return DiceRoller.roll(6, count, modifier)
    
    @staticmethod
    def d4(count: int = 1, modifier: int = 0) -> Dict:
        """Convenience method for d4 rolls"""
        return DiceRoller.roll(4, count, modifier)
    
    @staticmethod
    def d8(count: int = 1, modifier: int = 0) -> Dict:
        """Convenience method for d8 rolls"""
        return DiceRoller.roll(8, count, modifier)
    
    @staticmethod
    def d10(count: int = 1, modifier: int = 0) -> Dict:
        """Convenience method for d10 rolls"""
        return DiceRoller.roll(10, count, modifier)
    
    @staticmethod
    def d12(count: int = 1, modifier: int = 0) -> Dict:
        """Convenience method for d12 rolls"""
        return DiceRoller.roll(12, count, modifier)
    
    @staticmethod
    def ability_score_roll() -> Dict:
        """Roll ability scores (4d6, drop lowest)"""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls.sort(reverse=True)
        kept_rolls = rolls[:3]
        dropped = rolls[3]
        total = sum(kept_rolls)
        
        return {
            "rolls": rolls,
            "kept": kept_rolls,
            "dropped": dropped,
            "total": total,
            "description": "4d6 drop lowest",
            "modifier": 0,
            "sides": 6,
            "count": 4
        }
    
    @staticmethod
    def parse_and_roll(dice_string: str) -> Dict:
        """
        Parse dice notation and roll
        
        Supports formats like:
        - "1d20"
        - "2d6+3" 
        - "1d20-2"
        - "3d8+5"
        
        Args:
            dice_string: String in dice notation format
            
        Returns:
            Dice roll result dict
            
        Raises:
            ValueError: If format is invalid
        """
        dice_string = dice_string.strip().lower().replace(" ", "")
        
        # Regular expression to parse dice notation
        # Matches: XdY+Z, XdY-Z, XdY
        pattern = r'^(\d+)d(\d+)([+-]\d+)?$'
        match = re.match(pattern, dice_string)
        
        if not match:
            raise ValueError(f"Invalid dice format: {dice_string}. Use format like '1d20', '2d6+3'")
        
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier_str = match.group(3)
        
        modifier = 0
        if modifier_str:
            modifier = int(modifier_str)
        
        return DiceRoller.roll(sides, count, modifier)
    
    @staticmethod
    def advantage() -> Dict:
        """Roll with advantage (2d20, take higher)"""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        total = max(roll1, roll2)
        
        return {
            "rolls": [roll1, roll2],
            "total": total,
            "modifier": 0,
            "description": "Advantage (2d20, take higher)",
            "advantage": True,
            "sides": 20,
            "count": 2
        }
    
    @staticmethod
    def disadvantage() -> Dict:
        """Roll with disadvantage (2d20, take lower)"""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        total = min(roll1, roll2)
        
        return {
            "rolls": [roll1, roll2],
            "total": total,
            "modifier": 0,
            "description": "Disadvantage (2d20, take lower)",
            "disadvantage": True,
            "sides": 20,
            "count": 2
        }
    
    @staticmethod
    def ability_check(ability_score: int, advantage: bool = False, disadvantage: bool = False) -> Dict:
        """
        Make an ability check with proper modifier
        
        Args:
            ability_score: The ability score (3-20)
            advantage: Roll with advantage
            disadvantage: Roll with disadvantage
            
        Returns:
            Ability check result
        """
        modifier = (ability_score - 10) // 2
        
        if advantage and not disadvantage:
            result = DiceRoller.advantage()
            result["modifier"] = modifier
            result["total"] += modifier
            result["description"] += f" + {modifier}" if modifier >= 0 else f" {modifier}"
        elif disadvantage and not advantage:
            result = DiceRoller.disadvantage()
            result["modifier"] = modifier
            result["total"] += modifier
            result["description"] += f" + {modifier}" if modifier >= 0 else f" {modifier}"
        else:
            result = DiceRoller.d20(modifier)
        
        result["ability_score"] = ability_score
        return result

# Convenience instance for easy importing
dice = DiceRoller()
