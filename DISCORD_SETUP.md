# Discord Bot Setup Guide

## 🤖 Creating Your Discord Bot

### Step 1: Create Discord Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "AI Dungeon Master" (or whatever you prefer)
4. Click "Create"

### Step 2: Create the Bot
1. Click "Bot" in the left sidebar
2. Click "Add Bot" → "Yes, do it!"
3. Under "Token", click "Copy" to copy your bot token
4. **Keep this token secret!**

### Step 3: Set Bot Permissions
1. Click "OAuth2" → "URL Generator" in the left sidebar
2. Under "Scopes", check:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under "Bot Permissions", check:
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Use External Emojis

### Step 4: Get Invite Link
1. Copy the generated URL at the bottom
2. Open it in a new tab
3. Select your Discord server
4. Click "Authorize"

## 🔧 Setting up the Code

### Step 1: Install Dependencies
```bash
pip install discord.py
```

### Step 2: Update .env File
Add your Discord bot token to `.env`:
```
DISCORD_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_key_here
DEFAULT_AI_PROVIDER=groq
```

### Step 3: Run the Bot
```bash
python main_discord.py
```

You should see:
```
🎲 AI Dungeon Master#1234 has entered the realm!
Bot is ready in 1 servers
Synced 7 slash commands
```

## 🎮 How to Play

### Starting a Campaign
```
/start "Epic Quest"
```

### Players Join
```
/join "Aragorn" "Fighter"
/join "Gandalf" "Wizard"  
/join "Legolas" "Ranger"
```

### Begin Adventure
```
/begin serious
```
(Options: serious, comedic, mysterious, chaotic)

### Gameplay
Players can now just type their actions naturally:
```
I search the ancient chest for traps
I cast fireball at the goblins
I try to persuade the guard to let us pass
```

Or use the slash command:
```
/action I search the ancient chest for traps
```

### Dice Rolling
```
/roll 1d20+5
/roll 2d6
/roll 1d8-1
```

### Other Commands
```
/players - Show all players
/help - Show commands
/end - End campaign
```

## 🎯 Bot Features

### ✅ What Works:
- **Turn-based multiplayer** - Players take turns automatically
- **Character creation** - Auto-rolled stats, multiple classes
- **AI DM responses** - Powered by Groq (fast & free!)
- **Automatic dice rolling** - Triggered by keywords like "attack", "search"
- **Multiple DM personalities** - Each with unique voice/style
- **Session persistence** - Games are saved automatically
- **Rich embeds** - Beautiful formatted messages
- **Slash commands** - Modern Discord interface

### 🚀 Multiplayer Magic:
- **Multiple campaigns** can run in different channels simultaneously
- **Turn order** is automatically managed
- **Player status** shows HP, current turn, etc.
- **Real-time responses** from the AI DM
- **Natural language actions** - just type what you want to do!

## 🐛 Troubleshooting

### Bot won't start:
- Check your `DISCORD_BOT_TOKEN` in .env
- Make sure you copied the full token
- Verify the bot is invited to your server

### Bot doesn't respond to commands:
- Make sure bot has permissions in the channel
- Try `/help` to see if slash commands work
- Check the console for error messages

### AI responses not working:
- Verify `GROQ_API_KEY` is set correctly
- Run `python debug_env.py` to test connection
- Bot will fall back to offline mode if API fails

## 🎊 Ready to Adventure!

Your Discord server now has an AI Dungeon Master! Gather your friends and start your epic campaign. The bot handles all the complexity while you focus on the fun of D&D storytelling.

**Pro tip:** Create a dedicated channel like `#dnd-campaign` for your games to keep things organized!
