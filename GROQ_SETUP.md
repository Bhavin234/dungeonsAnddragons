# Quick Groq Setup Guide

## Steps to get Groq working:

### 1. Install Groq
```bash
pip install groq
```

### 2. Get API Key
1. Go to https://console.groq.com/
2. Sign up (free)
3. Go to "API Keys" 
4. Create new key
5. Copy the key (starts with `gsk_...`)

### 3. Update your .env file
```bash
# Add this to your .env file:
GROQ_API_KEY=gsk_your_actual_key_here
DEFAULT_AI_PROVIDER=groq
```

### 4. Run the game
```bash
python main.py
```

You should see something like:
```
🎭 Master Aldric the Wise will be your Dungeon Master!
```

Instead of the offline mode message.

## Why Groq is Perfect:
- ⚡ **Super Fast**: 2-3x faster than OpenAI
- 💰 **Generous Free Tier**: 6,000 tokens/minute 
- 🧠 **Smart**: Uses Llama 3.1 70B (very capable)
- 🎮 **Gaming Optimized**: Great for creative content
- 🚫 **No Quota Issues**: Way more generous than OpenAI

## Models Available:
- `llama-3.1-8b-instant` (what we're using - fast and great for creative tasks)
- `llama-3.2-3b-preview` (newer, smaller model)
- `mixtral-8x7b-32768` (good alternative with larger context)

The game will automatically use Groq when you set `DEFAULT_AI_PROVIDER=groq`!
