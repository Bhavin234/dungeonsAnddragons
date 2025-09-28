# Railway/Render Deployment Guide

## Option 1: Railway (Recommended)

### Step 1: Prepare Repository
1. Commit all your changes to Git:
```bash
git add .
git commit -m "feat: Discord bot ready for deployment"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app/
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `dungeons&dragons` repository
5. Railway will auto-detect it's a Python app

### Step 3: Set Environment Variables
In Railway dashboard, go to Variables tab and add:
```
DISCORD_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_key_here
DEFAULT_AI_PROVIDER=groq
DEFAULT_CONTENT_RATING=teen
```

### Step 4: Deploy
- Railway automatically deploys when you push to main branch
- Your bot will be online 24/7!

## Option 2: Render

### Step 1: Create Render Account
1. Go to https://render.com/
2. Sign up with GitHub

### Step 2: Create Web Service  
1. Click "New" → "Web Service"
2. Connect your GitHub repo
3. Use these settings:
   - **Name**: `dnd-ai-bot`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main_discord.py`

### Step 3: Environment Variables
Add the same environment variables as Railway.

### Step 4: Deploy
Click "Create Web Service" - Render will build and deploy automatically.

## Option 3: Heroku (If you prefer)

### Step 1: Install Heroku CLI
Download from https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Create Heroku App
```bash
heroku create your-dnd-bot-name
```

### Step 3: Set Environment Variables
```bash
heroku config:set DISCORD_BOT_TOKEN=your_token_here
heroku config:set GROQ_API_KEY=your_groq_key_here
heroku config:set DEFAULT_AI_PROVIDER=groq
```

### Step 4: Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 🎯 **Recommended: Railway**

**Why Railway:**
- ✅ **Generous free tier** (500 hours/month)
- ✅ **Auto-deploys** on git push
- ✅ **Zero config** - just works
- ✅ **Great for Discord bots**
- ✅ **Easy environment variable management**

## 📊 **Monitoring Your Bot**

After deployment, monitor your bot:
- Check Railway/Render logs for errors
- Bot should show "online" status in Discord
- Test commands in your Discord server

## 🔄 **Auto-Deployment Setup**

Once deployed, every time you:
1. Make code changes
2. `git push origin main`
3. Railway/Render automatically redeploys
4. Bot restarts with new code

**Your bot will now run 24/7 without your computer!**
