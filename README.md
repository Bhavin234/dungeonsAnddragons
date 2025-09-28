# AI Dungeon Master

An AI-powered Dungeon Master for Dungeons & Dragons adventures using Large Language Models. This project demonstrates LLM integration, game state management, and provider-agnostic AI architecture - perfect for showcasing full-stack development skills.

## 🎮 Two Ways to Play

| Feature | CLI Version | Discord Bot Version |
|---------|-------------|--------------------|
| **Players** | Single-player | Multiplayer (unlimited) |
| **Interface** | Command line | Discord (rich embeds) |
| **Turn Management** | Manual | Automatic |
| **Character Sheets** | Text display | Rich embeds with stats |
| **Dice Rolling** | Manual commands | Auto-triggered + manual |
| **Best For** | Development/Testing | Playing with friends |
| **Setup Time** | 2 minutes | 5 minutes |

### 🖥️ Command Line Interface (CLI)
Single-player experience perfect for testing and development.

### 🤖 Discord Bot
Multiplayer D&D campaigns with your friends on Discord! Features turn-based gameplay, character management, and real-time AI responses.

## What Makes This Resume-Worthy

- **AI/LLM Integration**: Provider-agnostic architecture supporting OpenAI and Anthropic
- **Complex State Management**: Persistent game sessions with story memory
- **Robust Architecture**: Modular design with clear separation of concerns
- **Test-Driven Development**: Comprehensive test suite with CI/CD
- **Extensible Design**: Ready to scale from CLI → Discord Bot → Web App

## Features

- Multiple AI Dungeon Master personalities (Serious, Comedic, Mysterious, Chaotic)
- Persistent character progression and story memory
- Advanced dice rolling system with natural language parsing
- Turn-based combat encounters
- Content rating controls for appropriate gameplay
- Provider-agnostic AI integration (easily switch between OpenAI/Anthropic)

## Setup Instructions

### 1. Clone and Navigate
```bash
cd dungeons&dragons
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=your_actual_key_here
```

### 5. Run the CLI Game
```bash
python main.py
```

### 6. Or Run the Discord Bot
```bash
python main_discord.py
```

**For Discord Bot Setup:** See [DISCORD_SETUP.md](DISCORD_SETUP.md) for detailed instructions on creating and configuring your Discord bot.

### 7. Run Tests
```bash
pytest
```

## API Provider Configuration

### Using Groq (Recommended - Fast & Free!)
Set in your `.env` file:
```
GROQ_API_KEY=your_groq_key
DEFAULT_AI_PROVIDER=groq
```

**Why Groq?**
- ✅ 6,000 tokens/minute FREE tier
- ✅ Lightning-fast responses (2-3x faster than OpenAI)
- ✅ Llama 3.1 8B model (fast and capable)
- ✅ Perfect for gaming applications
- ✅ Much more generous limits than OpenAI

**Get your Groq API key:** https://console.groq.com/

### Using OpenAI (If you have credits)
Set in your `.env` file:
```
OPENAI_API_KEY=your_openai_key
DEFAULT_AI_PROVIDER=openai
```

### Using Anthropic/Claude
Set in your `.env` file:
```
ANTHROPIC_API_KEY=your_anthropic_key
DEFAULT_AI_PROVIDER=anthropic
```

### Using Offline Mode (No API Costs!)
For unlimited play without API costs, set in your `.env` file:
```
DEFAULT_AI_PROVIDER=offline
# or simply don't set any API keys
```

Offline mode uses intelligent keyword-based responses that adapt to:
- Different DM personalities
- Your dice roll results 
- Common D&D actions (attack, search, talk, etc.)
- Story context and character actions

**Perfect for testing, demos, or when you want to play without API limits!**

## Example Commands

Once running, try these commands:
- Character creation: Follow the prompts to create your adventurer
- Basic actions: "search the room", "talk to the innkeeper"
- Combat: "attack the goblin", "cast fireball"
- Dice rolling: "roll 1d20+5", "roll 2d6"
- System: "stats", "inventory", "help", "quit"

## Development

### Recommended Tools (Optional)
```bash
pip install black ruff  # For formatting and linting
black .                 # Format code
ruff check .           # Check for issues
```

### Project Structure
- `app/` - Core application modules
- `app/ai/` - AI provider integrations and prompts
- `app/core/` - Game logic (dice, characters, sessions)
- `app/adapters/` - Interface adapters (CLI, future Discord/Web)
- `tests/` - Test suite
- `sessions/` - Saved game sessions

### Adding New AI Providers
The `DungeonMaster` class in `app/ai/dm.py` is designed for easy extension. Simply add your provider logic in the `_call_ai()` method.

## Architecture Highlights

This project showcases several important software engineering concepts:
- **Adapter Pattern**: Clean separation between UI and game logic
- **Provider Pattern**: Swappable AI backends
- **Persistence Layer**: JSON-based session storage with easy migration path
- **Test Coverage**: Unit tests for critical game mechanics
- **CI/CD Pipeline**: Automated testing on every commit

Perfect for demonstrating modern Python development practices and AI integration skills!
