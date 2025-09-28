"""
Discord Bot Adapter for AI Dungeon Master
Handles Discord-specific interactions and multiplayer coordination
"""

import asyncio
import os
import discord
from discord.ext import commands
from typing import Dict, List, Optional
from dotenv import load_dotenv

from app.ai.dm import DungeonMaster
from app.ai.prompts import PERSONALITIES, CONTENT_RATINGS
from app.core.character import Character
from app.core.dice import DiceRoller
from app.core.session import GameSession
from app.core.encounter import Encounter, create_enemy

# Load environment variables
load_dotenv()

class DiscordGameSession:
    """Extended game session for Discord multiplayer"""
    
    def __init__(self, channel_id: int, session_id: str):
        self.channel_id = channel_id
        self.session_id = session_id
        self.session = GameSession(f"discord_{channel_id}_{session_id}")
        
        # Discord-specific data
        self.players: Dict[int, Character] = {}  # user_id -> Character
        self.dm: Optional[DungeonMaster] = None
        self.turn_queue: List[int] = []  # user_ids in turn order
        self.current_turn_index = 0
        self.is_active = False
        
        # Game state
        self.encounter: Optional[Encounter] = None
        self.dice = DiceRoller()
    
    def add_player(self, user_id: int, character: Character):
        """Add a player to the session"""
        self.players[user_id] = character
        if user_id not in self.turn_queue:
            self.turn_queue.append(user_id)
    
    def get_current_player(self) -> Optional[int]:
        """Get the user_id of the current player"""
        if not self.turn_queue or not self.is_active:
            return None
        return self.turn_queue[self.current_turn_index]
    
    def next_turn(self):
        """Advance to next player's turn"""
        if self.turn_queue:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_queue)
    
    def get_player_list(self) -> str:
        """Get formatted list of players"""
        if not self.players:
            return "No players joined yet."
        
        player_list = []
        for i, (user_id, char) in enumerate(self.players.items()):
            turn_indicator = " 👈" if self.is_active and user_id == self.get_current_player() else ""
            hp_status = f"{char.health}/{char.max_health} HP"
            player_list.append(f"{i+1}. <@{user_id}> - {char.name} the {char.character_class} ({hp_status}){turn_indicator}")
        
        return "\n".join(player_list)

class DnDBot(commands.Bot):
    """Discord bot for AI Dungeon Master"""
    
    def __init__(self):
        intents = discord.Intents.default()
        # Enable privileged intents since user has enabled them in Discord Developer Portal
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="AI-powered Dungeon Master for D&D adventures!"
        )
        
        # Store active game sessions per channel
        self.game_sessions: Dict[int, DiscordGameSession] = {}
        
        # Configuration
        self.provider = os.getenv("DEFAULT_AI_PROVIDER", "groq")
        self.content_rating = os.getenv("DEFAULT_CONTENT_RATING", "teen")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'🎲 {self.user} has entered the realm!')
        print(f'Bot is ready in {len(self.guilds)} servers')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} slash commands')
        except Exception as e:
            print(f'Failed to sync commands: {e}')
    
    async def on_message(self, message):
        """Handle regular messages for natural language actions"""
        if message.author == self.user:
            return
        
        # Check if this channel has an active game
        channel_id = message.channel.id
        if channel_id in self.game_sessions:
            game = self.game_sessions[channel_id]
            
            # Check if it's the player's turn (in active game)
            if game.is_active and message.author.id == game.get_current_player():
                # Handle as a game action
                await self.handle_game_action(message, game)
                return
        
        # Process regular bot commands
        await self.process_commands(message)
    
    async def handle_game_action(self, message, game: DiscordGameSession):
        """Handle a player's action during active gameplay"""
        user_id = message.author.id
        action = message.content.strip()
        
        if not action:
            return
        
        # Get player character
        character = game.players.get(user_id)
        if not character:
            await message.reply("❌ You're not in this game! Use `/join` to join.")
            return
        
        # Check for dice roll triggers
        dice_result = None
        action_lower = action.lower()
        dice_keywords = ['attack', 'hit', 'strike', 'fight', 'climb', 'jump', 'leap',
                        'persuade', 'convince', 'charm', 'search', 'look for', 'investigate',
                        'examine', 'lockpick', 'pick lock', 'open', 'sneak', 'stealth', 
                        'hide', 'cast', 'spell', 'magic']
        
        if any(keyword in action_lower for keyword in dice_keywords):
            dice_result = game.dice.d20()
            await message.reply(f"🎲 Rolling d20: **{dice_result['total']}**")
        
        # Add to session
        game.session.add_player_action(f"{message.author.display_name}: {action}", dice_result)
        
        # Get AI response
        context = game.session.get_context(10)
        response = game.dm.generate_response(context, action, dice_result)
        
        # Create embed for DM response
        embed = discord.Embed(
            title=f"🎭 {game.dm.get_personality_info()['name']}",
            description=response,
            color=0x7B68EE
        )
        
        await message.reply(embed=embed)
        game.session.add_dm_response(response, game.dm.personality)
        
        # Advance to next player's turn
        game.next_turn()
        
        # Show whose turn it is next
        next_player = game.get_current_player()
        if next_player and next_player != user_id:
            # Create action buttons for next player
            action_buttons = ActionButtonView(game, next_player)
            await message.channel.send(
                f"🎯 <@{next_player}>, it's your turn! Choose an action or type what you want to do:",
                view=action_buttons
            )

# Initialize bot instance
bot = DnDBot()

# Add reaction button view class
class ActionButtonView(discord.ui.View):
    """Interactive buttons for common D&D actions"""
    
    def __init__(self, game_session, user_id):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game_session = game_session
        self.user_id = user_id
    
    @discord.ui.button(label="Attack", emoji="⚔️", style=discord.ButtonStyle.red)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "I attack the nearest enemy with my weapon")
    
    @discord.ui.button(label="Explore", emoji="🧭", style=discord.ButtonStyle.green)
    async def explore_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "I explore the area around me")
    
    @discord.ui.button(label="Talk", emoji="💬", style=discord.ButtonStyle.blurple)
    async def talk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "I try to talk and communicate with anyone nearby")
    
    @discord.ui.button(label="Search", emoji="🔍", style=discord.ButtonStyle.secondary)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "I carefully search the immediate area for anything interesting")
    
    @discord.ui.button(label="Cast Spell", emoji="✨", style=discord.ButtonStyle.secondary)
    async def magic_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "I cast a spell or use magic")
    
    async def _handle_button_action(self, interaction: discord.Interaction, action: str):
        """Handle button press actions"""
        # Check if it's the player's turn
        if interaction.user.id != self.game_session.get_current_player():
            current_player = self.game_session.get_current_player()
            await interaction.response.send_message(
                f"❌ It's not your turn! It's <@{current_player}>'s turn.", 
                ephemeral=True
            )
            return
        
        # Disable all buttons after use
        for item in self.children:
            item.disabled = True
        
        # Check for dice roll
        dice_result = None
        dice_keywords = ['attack', 'cast', 'search']
        if any(keyword in action.lower() for keyword in dice_keywords):
            dice_result = self.game_session.dice.d20()
        
        # Add action to session
        self.game_session.session.add_player_action(
            f"{interaction.user.display_name}: {action}", 
            dice_result
        )
        
        # Defer response for AI call
        await interaction.response.defer()
        
        # Get AI response
        context = self.game_session.session.get_context(10)
        ai_response = self.game_session.dm.generate_response(context, action, dice_result)
        
        # Create response embed
        embed = discord.Embed(
            title=f"🎭 {self.game_session.dm.get_personality_info()['name']}",
            description=ai_response,
            color=0x7B68EE
        )
        
        dice_text = f"\n🎲 Rolling d20: **{dice_result['total']}**" if dice_result else ""
        response_text = f"**{interaction.user.display_name}:** {action}{dice_text}"
        
        await interaction.edit_original_response(
            content=response_text,
            embed=embed,
            view=self  # Show disabled buttons
        )
        
        self.game_session.session.add_dm_response(ai_response, self.game_session.dm.personality)
        
        # Next turn
        self.game_session.next_turn()
        next_player = self.game_session.get_current_player()
        
        if next_player and next_player != interaction.user.id:
            # Send new action buttons for next player
            new_view = ActionButtonView(self.game_session, next_player)
            await interaction.channel.send(
                f"🎯 <@{next_player}>, it's your turn! Choose an action or type what you want to do:",
                view=new_view
            )

@bot.tree.command(name="start", description="Start a new D&D campaign")
async def start_campaign(interaction: discord.Interaction, name: str):
    """Start a new campaign"""
    channel_id = interaction.channel.id
    
    # Check if there's already an active game
    if channel_id in bot.game_sessions:
        await interaction.response.send_message("❌ There's already a campaign running in this channel! Use `/end` to end it first.")
        return
    
    # Create new game session
    game = DiscordGameSession(channel_id, name)
    bot.game_sessions[channel_id] = game
    
    embed = discord.Embed(
        title="🏰 New D&D Campaign Started!",
        description=f"**Campaign:** {name}\n\nUse `/join` to create your character and join the adventure!",
        color=0x00FF00
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="Show server statistics and leaderboards")
async def stats_command(interaction: discord.Interaction):
    """Show server stats and leaderboards"""
    embed = discord.Embed(
        title="📊 Server D&D Statistics",
        description=f"Statistics for {interaction.guild.name}",
        color=0xFFD700
    )
    
    # Count active campaigns
    server_campaigns = sum(1 for game in bot.game_sessions.values() 
                          if interaction.guild.get_channel(game.channel_id) is not None)
    
    # Count total players across all server campaigns
    total_players = 0
    active_players = 0
    for game in bot.game_sessions.values():
        if interaction.guild.get_channel(game.channel_id) is not None:
            total_players += len(game.players)
            if game.is_active:
                active_players += len(game.players)
    
    embed.add_field(
        name="🏠 Campaign Stats",
        value=f"• **Active Campaigns:** {server_campaigns}\n• **Total Players:** {total_players}\n• **Currently Playing:** {active_players}",
        inline=False
    )
    
    # Most popular DM personalities
    dm_usage = {}
    for game in bot.game_sessions.values():
        if game.dm and interaction.guild.get_channel(game.channel_id) is not None:
            personality = game.dm.personality
            dm_usage[personality] = dm_usage.get(personality, 0) + 1
    
    if dm_usage:
        popular_dms = sorted(dm_usage.items(), key=lambda x: x[1], reverse=True)[:3]
        dm_text = "\n".join([f"• **{PERSONALITIES[dm]['name']}:** {count} campaigns" 
                            for dm, count in popular_dms])
        embed.add_field(
            name="🎭 Popular DM Personalities",
            value=dm_text,
            inline=False
        )
    
    # Bot-wide stats
    embed.add_field(
        name="🤖 Bot Stats",
        value=f"• **Total Servers:** {len(bot.guilds)}\n• **Global Campaigns:** {len(bot.game_sessions)}\n• **Response Time:** <2 seconds",
        inline=False
    )
    
    embed.set_footer(text="Stats update in real-time!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="save", description="Manually save the current campaign")
async def save_command(interaction: discord.Interaction):
    """Manually save campaign"""
    channel_id = interaction.channel.id
    
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel!")
        return
    
    game = bot.game_sessions[channel_id]
    
    # Save the session
    success = game.session.save_session()
    
    if success:
        embed = discord.Embed(
            title="💾 Campaign Saved!",
            description="Your adventure progress has been saved.",
            color=0x00FF00
        )
        embed.add_field(
            name="Session Info",
            value=f"• **Campaign:** {game.session_id}\n• **Turn:** {game.session.turn_count}\n• **Players:** {len(game.players)}",
            inline=False
        )
    else:
        embed = discord.Embed(
            title="❌ Save Failed",
            description="There was an error saving your campaign.",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="join", description="Join the current campaign")
async def join_campaign(interaction: discord.Interaction, character_name: str, character_class: str):
    """Join the current campaign"""
    channel_id = interaction.channel.id
    user_id = interaction.user.id
    
    # Check if there's an active game
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel! Use `/start` to begin one.")
        return
    
    game = bot.game_sessions[channel_id]
    
    # Check if player already joined
    if user_id in game.players:
        await interaction.response.send_message("❌ You're already in this campaign!")
        return
    
    # Validate class
    valid_classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Ranger", "Paladin", 
                    "Barbarian", "Bard", "Druid", "Monk", "Sorcerer", "Warlock"]
    
    if character_class.title() not in valid_classes:
        class_list = ", ".join(valid_classes)
        await interaction.response.send_message(f"❌ Invalid class! Choose from: {class_list}")
        return
    
    # Create character with rolled stats
    abilities = {}
    ability_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    
    for ability in ability_names:
        roll_result = game.dice.ability_score_roll()
        abilities[ability] = roll_result["total"]
    
    character = Character(
        name=character_name,
        character_class=character_class.title(),
        **abilities
    )
    
    # Add player to game
    game.add_player(user_id, character)
    
    # Create character sheet embed
    embed = discord.Embed(
        title=f"⚔️ {character.name} the {character.character_class}",
        color=0x4169E1
    )
    
    embed.add_field(
        name="Stats",
        value=f"**HP:** {character.health}/{character.max_health}\n**AC:** {character.armor_class}\n**Gold:** {character.gold}",
        inline=True
    )
    
    embed.add_field(
        name="Abilities",
        value=f"**STR:** {character.strength}\n**DEX:** {character.dexterity}\n**CON:** {character.constitution}",
        inline=True
    )
    
    embed.add_field(
        name="",
        value=f"**INT:** {character.intelligence}\n**WIS:** {character.wisdom}\n**CHA:** {character.charisma}",
        inline=True
    )
    
    await interaction.response.send_message(f"✅ {interaction.user.mention} joined as:", embed=embed)

@bot.tree.command(name="players", description="Show all players in the campaign")
async def show_players(interaction: discord.Interaction):
    """Show all players"""
    channel_id = interaction.channel.id
    
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel!")
        return
    
    game = bot.game_sessions[channel_id]
    
    embed = discord.Embed(
        title="👥 Campaign Players",
        description=game.get_player_list(),
        color=0x9932CC
    )
    
    if game.is_active:
        embed.add_field(name="Status", value="🎮 Game Active", inline=False)
    else:
        embed.add_field(name="Status", value="⏸️ Waiting to Begin", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="begin", description="Begin the adventure with a chosen DM personality")
async def begin_adventure(interaction: discord.Interaction, dm_personality: str = "serious"):
    """Begin the adventure"""
    channel_id = interaction.channel.id
    
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel!")
        return
    
    game = bot.game_sessions[channel_id]
    
    if not game.players:
        await interaction.response.send_message("❌ No players have joined yet! Use `/join` to add players.")
        return
    
    # Validate personality
    if dm_personality not in PERSONALITIES:
        personality_list = ", ".join(PERSONALITIES.keys())
        await interaction.response.send_message(f"❌ Invalid DM personality! Choose from: {personality_list}")
        return
    
    # Initialize DM
    try:
        game.dm = DungeonMaster(
            provider=bot.provider,
            personality=dm_personality,
            content_rating=bot.content_rating
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to initialize AI DM: {e}")
        return
    
    # Start the game
    game.is_active = True
    
    # Defer the response since AI call might take time
    await interaction.response.defer()
    
    # Generate opening scene
    player_names = [char.name for char in game.players.values()]
    initial_prompt = f"Begin a new D&D adventure for these heroes: {', '.join(player_names)}. Create an engaging opening scene that brings them together."
    
    response = game.dm.generate_response("", initial_prompt)
    game.session.add_dm_response(response, game.dm.personality)
    
    # Create adventure start embed
    embed = discord.Embed(
        title="🌟 The Adventure Begins!",
        description=f"**DM:** {game.dm.get_personality_info()['name']}\n\n{response}",
        color=0xFF6347
    )
    
    embed.add_field(
        name="Turn Order",
        value=game.get_player_list(),
        inline=False
    )
    
    current_player = game.get_current_player()
    embed.add_field(
        name="Current Turn",
        value=f"<@{current_player}> - Just type your action in chat! (or use `/action`)",
        inline=False
    )
    
    # Create action buttons for the first player
    action_buttons = ActionButtonView(game, current_player)
    
    await interaction.followup.send(embed=embed)
    await interaction.channel.send(
        f"🎯 <@{current_player}>, it's your turn! Choose an action or type what you want to do:",
        view=action_buttons
    )

@bot.tree.command(name="roll", description="Roll dice")
async def roll_dice(interaction: discord.Interaction, dice: str):
    """Roll dice"""
    channel_id = interaction.channel.id
    
    try:
        roller = DiceRoller()
        result = roller.parse_and_roll(dice)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=0xFFD700
        )
        
        if len(result['rolls']) > 1:
            rolls_display = f"[{', '.join(map(str, result['rolls']))}]"
        else:
            rolls_display = str(result['rolls'][0])
        
        modifier_display = ""
        if result['modifier'] > 0:
            modifier_display = f" + {result['modifier']}"
        elif result['modifier'] < 0:
            modifier_display = f" - {abs(result['modifier'])}"
        
        embed.add_field(
            name=result['description'],
            value=f"{rolls_display}{modifier_display} = **{result['total']}**",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
    except ValueError as e:
        await interaction.response.send_message(f"❌ Invalid dice format: {e}\nExample: `1d20+3`, `2d6`, `1d8-1`")

@bot.tree.command(name="action", description="Take an action in the current game")
async def take_action(interaction: discord.Interaction, description: str):
    """Take a game action"""
    channel_id = interaction.channel.id
    user_id = interaction.user.id
    
    # Check if there's an active game
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel!")
        return
    
    game = bot.game_sessions[channel_id]
    
    # Check if game is active
    if not game.is_active:
        await interaction.response.send_message("❌ Game hasn't started yet! Use `/begin` to start.")
        return
    
    # Check if it's the player's turn
    if user_id != game.get_current_player():
        current_player = game.get_current_player()
        await interaction.response.send_message(f"❌ It's not your turn! It's <@{current_player}>'s turn.")
        return
    
    # Get player character
    character = game.players.get(user_id)
    if not character:
        await interaction.response.send_message("❌ You're not in this game! Use `/join` to join.")
        return
    
    # Check for dice roll triggers
    dice_result = None
    action_lower = description.lower()
    dice_keywords = ['attack', 'hit', 'strike', 'fight', 'climb', 'jump', 'leap',
                    'persuade', 'convince', 'charm', 'search', 'look for', 'investigate',
                    'examine', 'lockpick', 'pick lock', 'open', 'sneak', 'stealth', 
                    'hide', 'cast', 'spell', 'magic']
    
    dice_message = ""
    if any(keyword in action_lower for keyword in dice_keywords):
        dice_result = game.dice.d20()
        dice_message = f"\n🎲 Rolling d20: **{dice_result['total']}**"
    
    # Add to session
    game.session.add_player_action(f"{interaction.user.display_name}: {description}", dice_result)
    
    # Get AI response (this might take a moment)
    await interaction.response.defer()
    
    context = game.session.get_context(10)
    response = game.dm.generate_response(context, description, dice_result)
    
    # Create embed for DM response
    embed = discord.Embed(
        title=f"🎭 {game.dm.get_personality_info()['name']}",
        description=response,
        color=0x7B68EE
    )
    
    message_content = f"**{interaction.user.display_name}:** {description}{dice_message}"
    
    await interaction.followup.send(content=message_content, embed=embed)
    game.session.add_dm_response(response, game.dm.personality)
    
    # Advance to next player's turn
    game.next_turn()
    
    # Show whose turn it is next
    next_player = game.get_current_player()
    if next_player and next_player != user_id:
        await interaction.channel.send(f"🎯 <@{next_player}>, it's your turn! Use `/action` to describe what you do.")

@bot.tree.command(name="end", description="End the current campaign")
async def end_campaign(interaction: discord.Interaction):
    """End the current campaign"""
    channel_id = interaction.channel.id
    
    if channel_id not in bot.game_sessions:
        await interaction.response.send_message("❌ No active campaign in this channel!")
        return
    
    game = bot.game_sessions[channel_id]
    
    # Save session
    game.session.save_session()
    
    # Remove from active sessions
    del bot.game_sessions[channel_id]
    
    embed = discord.Embed(
        title="🏁 Campaign Ended",
        description="The adventure has concluded. Thanks for playing!",
        color=0x8B0000
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Show help"""
    embed = discord.Embed(
        title="🎲 AI Dungeon Master Commands",
        color=0x7B68EE
    )
    
    embed.add_field(
        name="Campaign Management",
        value="`/start <name>` - Start new campaign\n`/join <name> <class>` - Join campaign\n`/begin <personality>` - Begin adventure\n`/end` - End campaign",
        inline=False
    )
    
    embed.add_field(
        name="Gameplay", 
        value="`/roll <dice>` - Roll dice (e.g., 1d20+3)\n`/action <description>` - Take your turn (optional)\n`/players` - Show all players\n\n**Natural Language:** Just type your action when it's your turn!",
        inline=False
    )
    
    embed.add_field(
        name="DM Personalities",
        value="serious, comedic, mysterious, chaotic, sarcastic",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="about", description="Learn about this AI Dungeon Master bot")
async def about_command(interaction: discord.Interaction):
    """About the bot"""
    embed = discord.Embed(
        title="🤖 About AI Dungeon Master",
        description="An advanced AI-powered Dungeon Master that creates dynamic D&D adventures tailored to your choices.",
        color=0x00FF7F
    )
    
    embed.add_field(
        name="🎆 What Makes This Special",
        value="• **True Player Agency** - Make any choice, AI adapts\n• **Multiple DM Personalities** - Each with unique voice\n• **Smart Dice Integration** - Rolls when needed\n• **Persistent Campaigns** - Stories continue across sessions\n• **Natural Language** - Just type what you want to do",
        inline=False
    )
    
    embed.add_field(
        name="🤖 Powered By",
        value="• **Groq AI** (Lightning-fast responses)\n• **Advanced Prompt Engineering**\n• **Discord.py** (Seamless integration)\n• **Smart State Management**",
        inline=False
    )
    
    embed.add_field(
        name="📊 Stats",
        value=f"• **Servers:** {len(bot.guilds)}\n• **Active Campaigns:** {len(bot.game_sessions)}\n• **Uptime:** 24/7 hosted\n• **Response Time:** <2 seconds",
        inline=False
    )
    
    embed.set_footer(text="Built with ❤️ for D&D enthusiasts | Use /help to get started")
    
    await interaction.response.send_message(embed=embed)

def run_discord_bot():
    """Run the Discord bot"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please add your Discord bot token to the .env file")
        return
    
    bot.run(token)

if __name__ == "__main__":
    run_discord_bot()
