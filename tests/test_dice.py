"""
Tests for dice rolling system
"""

import pytest
from app.core.dice import DiceRoller

class TestDiceRoller:
    """Test cases for the DiceRoller class"""
    
    def test_basic_roll(self):
        """Test basic dice rolling"""
        result = DiceRoller.roll(6, 1, 0)
        
        assert isinstance(result, dict)
        assert "rolls" in result
        assert "total" in result
        assert "modifier" in result
        assert "description" in result
        
        assert isinstance(result["total"], int)
        assert 1 <= result["rolls"][0] <= 6
        assert result["total"] == result["rolls"][0] + result["modifier"]
    
    def test_roll_with_modifier(self):
        """Test rolling with positive and negative modifiers"""
        # Positive modifier
        result = DiceRoller.roll(6, 1, 3)
        assert result["modifier"] == 3
        assert result["total"] == result["rolls"][0] + 3
        
        # Negative modifier
        result = DiceRoller.roll(6, 1, -2)
        assert result["modifier"] == -2
        assert result["total"] == result["rolls"][0] - 2
    
    def test_multiple_dice(self):
        """Test rolling multiple dice"""
        result = DiceRoller.roll(6, 3, 0)
        
        assert len(result["rolls"]) == 3
        assert all(1 <= roll <= 6 for roll in result["rolls"])
        assert result["total"] == sum(result["rolls"])
    
    def test_d20_convenience(self):
        """Test d20 convenience method"""
        result = DiceRoller.d20()
        
        assert len(result["rolls"]) == 1
        assert 1 <= result["rolls"][0] <= 20
        assert result["sides"] == 20
        assert result["count"] == 1
    
    def test_d20_with_modifier(self):
        """Test d20 with modifier"""
        result = DiceRoller.d20(5)
        
        assert result["modifier"] == 5
        assert result["total"] == result["rolls"][0] + 5
    
    def test_parse_and_roll_basic(self):
        """Test parsing basic dice notation"""
        result = DiceRoller.parse_and_roll("1d20")
        
        assert len(result["rolls"]) == 1
        assert 1 <= result["rolls"][0] <= 20
        assert result["modifier"] == 0
        assert result["total"] == result["rolls"][0]
    
    def test_parse_and_roll_with_positive_modifier(self):
        """Test parsing dice notation with positive modifier"""
        result = DiceRoller.parse_and_roll("1d6+3")
        
        assert len(result["rolls"]) == 1
        assert 1 <= result["rolls"][0] <= 6
        assert result["modifier"] == 3
        assert result["total"] == result["rolls"][0] + 3
    
    def test_parse_and_roll_with_negative_modifier(self):
        """Test parsing dice notation with negative modifier"""
        result = DiceRoller.parse_and_roll("2d8-2")
        
        assert len(result["rolls"]) == 2
        assert all(1 <= roll <= 8 for roll in result["rolls"])
        assert result["modifier"] == -2
        assert result["total"] == sum(result["rolls"]) - 2
    
    def test_parse_and_roll_multiple_dice(self):
        """Test parsing multiple dice"""
        result = DiceRoller.parse_and_roll("3d6")
        
        assert len(result["rolls"]) == 3
        assert all(1 <= roll <= 6 for roll in result["rolls"])
        assert result["total"] == sum(result["rolls"])
    
    def test_parse_and_roll_invalid_format(self):
        """Test parsing invalid dice notation"""
        with pytest.raises(ValueError):
            DiceRoller.parse_and_roll("invalid")
        
        with pytest.raises(ValueError):
            DiceRoller.parse_and_roll("1d")
        
        with pytest.raises(ValueError):
            DiceRoller.parse_and_roll("d6")
    
    def test_ability_score_roll(self):
        """Test ability score rolling (4d6 drop lowest)"""
        result = DiceRoller.ability_score_roll()
        
        assert len(result["rolls"]) == 4
        assert len(result["kept"]) == 3
        assert result["total"] == sum(result["kept"])
        assert all(1 <= roll <= 6 for roll in result["rolls"])
        assert 3 <= result["total"] <= 18
    
    def test_advantage_roll(self):
        """Test advantage rolling"""
        result = DiceRoller.advantage()
        
        assert len(result["rolls"]) == 2
        assert all(1 <= roll <= 20 for roll in result["rolls"])
        assert result["total"] == max(result["rolls"])
        assert result["advantage"] is True
    
    def test_disadvantage_roll(self):
        """Test disadvantage rolling"""
        result = DiceRoller.disadvantage()
        
        assert len(result["rolls"]) == 2
        assert all(1 <= roll <= 20 for roll in result["rolls"])
        assert result["total"] == min(result["rolls"])
        assert result["disadvantage"] is True
    
    def test_ability_check(self):
        """Test ability check mechanics"""
        result = DiceRoller.ability_check(16)  # +3 modifier
        
        assert result["ability_score"] == 16
        assert result["modifier"] == 3
        assert result["total"] == result["rolls"][0] + 3
    
    def test_ability_check_with_advantage(self):
        """Test ability check with advantage"""
        result = DiceRoller.ability_check(14, advantage=True)  # +2 modifier
        
        assert result["ability_score"] == 14
        assert result["modifier"] == 2
        assert len(result["rolls"]) == 2
        assert result["total"] == max(result["rolls"]) + 2
    
    def test_ability_check_with_disadvantage(self):
        """Test ability check with disadvantage"""
        result = DiceRoller.ability_check(12, disadvantage=True)  # +1 modifier
        
        assert result["ability_score"] == 12
        assert result["modifier"] == 1
        assert len(result["rolls"]) == 2
        assert result["total"] == min(result["rolls"]) + 1
    
    def test_invalid_parameters(self):
        """Test error handling for invalid parameters"""
        with pytest.raises(ValueError):
            DiceRoller.roll(0, 1, 0)  # Zero sides
        
        with pytest.raises(ValueError):
            DiceRoller.roll(6, 0, 0)  # Zero count
        
        with pytest.raises(ValueError):
            DiceRoller.roll(-1, 1, 0)  # Negative sides
    
    def test_description_formatting(self):
        """Test that descriptions are formatted correctly"""
        result1 = DiceRoller.roll(6, 1, 0)
        assert result1["description"] == "1d6"
        
        result2 = DiceRoller.roll(8, 2, 3)
        assert result2["description"] == "2d8+3"
        
        result3 = DiceRoller.roll(20, 1, -2)
        assert result3["description"] == "1d20-2"

class TestDiceConvenienceMethods:
    """Test convenience methods for common dice"""
    
    def test_d4(self):
        """Test d4 convenience method"""
        result = DiceRoller.d4()
        assert 1 <= result["rolls"][0] <= 4
        assert result["sides"] == 4
    
    def test_d6(self):
        """Test d6 convenience method"""
        result = DiceRoller.d6(2, 1)
        assert len(result["rolls"]) == 2
        assert all(1 <= roll <= 6 for roll in result["rolls"])
        assert result["modifier"] == 1
    
    def test_d8(self):
        """Test d8 convenience method"""
        result = DiceRoller.d8()
        assert 1 <= result["rolls"][0] <= 8
        assert result["sides"] == 8
    
    def test_d10(self):
        """Test d10 convenience method"""
        result = DiceRoller.d10()
        assert 1 <= result["rolls"][0] <= 10
        assert result["sides"] == 10
    
    def test_d12(self):
        """Test d12 convenience method"""
        result = DiceRoller.d12()
        assert 1 <= result["rolls"][0] <= 12
        assert result["sides"] == 12

if __name__ == "__main__":
    pytest.main([__file__])
