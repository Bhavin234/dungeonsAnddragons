# AI Dungeon Master - Technical Explanation

This document explains the architecture and implementation details of the AI Dungeon Master project.

## Project Overview

The AI Dungeon Master is a command-line D&D game powered by Large Language Models. It demonstrates modern software engineering practices including provider-agnostic AI integration, persistent state management, and test-driven development.

## File Structure Explanation

### Root Directory Files

- **`main.py`**: Entry point that imports and calls the CLI runner
- **`requirements.txt`**: Python dependencies for the project
- **`.env.example`**: Template for environment variables (API keys, configuration)
- **`.gitignore`**: Git ignore patterns for Python projects and secrets
- **`README.md`**: Project documentation and setup instructions

### App Structure (`app/`)

The application follows a layered architecture pattern:

#### AI Layer (`app/ai/`)
- **`dm.py`**: The `DungeonMaster` class - provider-agnostic wrapper for AI APIs
  - Handles OpenAI integration with clear extension points for Anthropic/Claude
  - Manages system prompts, error handling, and fallback responses
  - Abstracts AI provider differences behind a consistent interface

- **`prompts.py`**: Centralized prompt management
  - Base system prompts that work with all personalities
  - Personality-specific prompt modifications (Serious, Comedic, Mysterious, Chaotic)
  - Content rating system (Family, Teen, Mature) for appropriate responses
  - Fallback response generation for when AI calls fail

#### Core Game Logic (`app/core/`)
- **`dice.py`**: Complete D&D dice system
  - Parse natural language dice notation ("1d20+3", "2d6-1") 
  - Convenience methods for standard dice (d4, d6, d8, d10, d12, d20)
  - Advanced mechanics: advantage/disadvantage, ability checks, ability score generation
  - Structured return format with rolls, totals, and descriptions

- **`character.py`**: Full character management system
  - D&D-style ability scores with calculated modifiers
  - Health, armor class, inventory, and gold tracking
  - Leveling system with experience points and HP increases
  - Status conditions and temporary effects
  - Serialization for persistent character storage

- **`session.py`**: Game state persistence and story memory
  - `StoryEvent` dataclass for structured event storage
  - `GameSession` class managing turn-by-turn story progression
  - Context generation for AI (last N events formatted for prompt)
  - Automatic save functionality every few turns
  - JSON-based persistence with Unicode support

- **`encounter.py`**: Turn-based combat system
  - `Combatant` class representing any fighting entity
  - `Encounter` class managing initiative, turn order, and combat flow
  - Attack resolution with dice rolling and damage calculation
  - Spell casting framework with various effect types
  - Pre-defined enemy templates for quick encounter creation

#### Interface Layer (`app/adapters/`)
- **`cli_adapter.py`**: Command-line interface implementation
  - Bridges between user input/output and core game systems
  - Handles all CLI-specific logic (prompts, formatting, help text)
  - Command parsing and routing to appropriate handlers
  - Game setup flow (character creation, session loading, DM selection)
  - Error handling and graceful degradation when AI fails

#### CLI Entry Point (`app/`)
- **`cli.py`**: Thin wrapper that instantiates and runs the CLI adapter

### Testing (`tests/`)
- **`test_dice.py`**: Comprehensive dice system tests
  - Tests all dice rolling mechanics and edge cases
  - Validates parsing of dice notation
  - Ensures statistical validity of random generation

- **`test_session.py`**: Session persistence and story management tests
  - Tests save/load functionality with various data scenarios
  - Validates story event creation and context generation
  - Tests error handling for corrupted or missing session files

### Infrastructure
- **`.github/workflows/python-app.yml`**: CI/CD pipeline
  - Runs on Python 3.11 with Ubuntu
  - Installs dependencies and runs pytest
  - Validates code on every push/PR

- **`sessions/`**: Runtime directory for saved game sessions

## Game Flow - "What Happens When Player Types X"

Here's the step-by-step flow when a player inputs an action:

1. **Input Reception** (`cli_adapter.py`)
   - CLI adapter receives raw user input
   - Checks if input is a system command (quit, help, stats, etc.)

2. **Command Processing**
   - System commands are handled immediately (show stats, roll dice, etc.)
   - Game actions proceed to action handling

3. **Dice Roll Detection** (`cli_adapter.py`)
   - Scans input for action keywords that trigger dice rolls
   - Keywords like "attack", "climb", "persuade" automatically trigger d20 roll
   - Roll result is captured for inclusion in AI prompt

4. **Session Update** (`session.py`)
   - Player action is added to story history with timestamp
   - If dice were rolled, separate dice event is also recorded
   - Turn counter increments, potentially triggering auto-save

5. **Context Preparation** (`session.py`)
   - Recent story events (last 10) are formatted into context string
   - Current location, NPCs, combat status are included
   - Context provides AI with story continuity

6. **AI Generation** (`dm.py`)
   - Context, player action, and dice result are sent to AI provider
   - System prompt combines base guidelines + personality + content rating
   - AI generates contextual response or fallback is used on failure

7. **Response Processing** (`cli_adapter.py`)
   - DM response is displayed to player with personality indicator
   - Response is added to session history
   - System checks for special triggers (combat initiation, etc.)

8. **Special Event Handling**
   - Combat keywords can trigger encounter creation
   - Other special events update game state accordingly

9. **Prompt Display**
   - Game status (health, location, combat indicator) is shown
   - Player is prompted for next action, loop continues

## Key Design Decisions

### Provider-Agnostic AI
The `DungeonMaster` class abstracts AI provider differences. Adding new providers requires implementing `_init_[provider]()` and `_call_[provider]()` methods without changing other code.

### Event-Driven Architecture
All game events are stored as structured `StoryEvent` objects, making it easy to replay, export, or analyze gameplay sessions.

### Graceful Degradation
When AI calls fail, the system provides contextual fallback responses and continues operation rather than crashing.

### Modular Design
Each system (dice, character, session, combat) is independent and testable, following single responsibility principle.

### Test Coverage
Critical game mechanics have comprehensive test suites ensuring reliability and facilitating refactoring.

This architecture makes the project easily extensible - adding Discord bot functionality would involve creating `app/adapters/discord_adapter.py` while reusing all core game logic.
