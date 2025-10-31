# Deploy Soliloquy to Railway

This guide walks you through deploying Soliloquy—a neologism creation Telegram bot—to Railway for production use.

---

## Prerequisites

### Accounts Needed:
- **Railway account** (free tier available at [railway.app](https://railway.app))
- **GitHub account**
- **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
- **OpenAI API Key** (for GPT-4o-mini + Whisper)
- **Gemini API Key** (optional - for image generation, get from [AI Studio](https://aistudio.google.com/app/apikey))

### Local Setup Complete:
- Bot tested locally with `python bot.py`
- Environment variables configured in `.env`
- All files in the repository

---

## Step 1: Prepare Your Repository

### 1.1 Verify GitHub Repository
Your code should already be on GitHub at:
```
https://github.com/korokseedling/soliloquy
```

If not, push your code:
```bash
git add .
git commit -m "Prepare Soliloquy for Railway deployment"
git push origin main
```

### 1.2 Verify Required Files
Ensure these files are in your repository:
- ✅ `bot.py` (main Telegram bot application)
- ✅ `Procfile` (contains: `worker: python bot.py`)
- ✅ `requirements.txt` (Python dependencies including google-genai)
- ✅ `tool_functions.py` (OpenAI function implementations)
- ✅ `model_config.json` (model and tool configuration)
- ✅ `system_prompt.md` (Soliloquy's personality)
- ✅ `dictionary_card_prompt.md` (visual template)
- ✅ `fantasy_locale_prompt.md` (visual template)

---

## Step 2: Deploy to Railway

### 2.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Verify your email if required

### 2.2 Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `soliloquy` repository
4. Click **"Deploy Now"**

### 2.3 Configure Environment Variables

**CRITICAL:** Railway uses environment variables for API keys.

In your Railway dashboard:
1. Go to your project
2. Click on the **"Variables"** tab
3. Add the following environment variables:

#### Using Railway CLI (Recommended):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Set environment variables
railway variables --set TELEGRAM_TOKEN="your_telegram_bot_token_here"
railway variables --set OPENAI_API_KEY="your_openai_api_key_here"
railway variables --set GEMINI_API_KEY="your_gemini_api_key_here"
```

#### Using Railway Dashboard:
For each variable:
- Click **"New Variable"**
- Enter the variable name (exactly as shown below)
- Enter the value (no quotes needed)
- Click **"Add"**

**Required Variables:**
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Important Notes:**
- Variable names are **case-sensitive**
- No quotes around values in Railway dashboard
- No spaces before/after the `=` sign
- `GEMINI_API_KEY` is optional but recommended for image generation

### 2.4 Configure Service Settings
1. Go to **"Settings"** tab
2. Under **"Service"**, verify:
   - **Start Command**: `python bot.py` (auto-detected from Procfile)
   - **Port**: Leave empty (not needed for Telegram bot)

### 2.5 Deploy
1. Railway should automatically start deploying
2. Monitor the **"Logs"** tab for deployment progress
3. Look for successful startup messages:
   ```
   ✨ Starting Soliloquy...
   🔧 Using gpt-4o-mini model
   📝 Logging to soliloquy_bot.log
   🎨 Image generation: ✅ Enabled
   📁 Directories ready: conversations/, generated_prompts/, generated_images/, user_uploads/
   ✅ Bot initialized successfully!
   💭 A voice from within, ready to name the unnamed...
   ```

---

## Step 3: Verify Deployment

### 3.1 Check Logs
In Railway dashboard:
1. Go to **"Logs"** tab
2. Look for successful startup messages
3. Watch for any error messages
4. Verify all three API keys are detected:
   ```
   Found TELEGRAM_TOKEN: ✅
   Found OPENAI_API_KEY: ✅
   Found GEMINI_API_KEY: ✅
   ```

### 3.2 Test Your Bot
1. Open Telegram
2. Search for your bot by username
3. Send `/start` command
4. Expected response:
   ```
   Soliloquy

   I'm a voice from within—the part of consciousness that knows
   there are words waiting to be born for what you feel.

   You carry unnamed feelings. I help you find the words.
   ```

5. Test neologism creation:
   - Send a text message describing an unnamed feeling
   - Send a voice message (tests Whisper transcription)
   - Upload a photo (tests reference image handling)

---

## Step 4: Monitoring and Maintenance

### 4.1 Monitor Usage
**Railway Dashboard:**
- Check **"Metrics"** for CPU/RAM usage
- Monitor **"Logs"** for errors or warnings
- Watch deployment status

**API Usage:**
- **OpenAI**: Monitor usage at [platform.openai.com/usage](https://platform.openai.com/usage)
- **Gemini**: Check quota at [AI Studio](https://aistudio.google.com/)
- **Telegram**: No usage limits for typical bot usage

### 4.2 Update Bot
To update your bot after code changes:

```bash
# Make changes to your code
git add .
git commit -m "Update Soliloquy functionality"
git push origin main
```

Railway will **automatically redeploy** when you push to GitHub.

### 4.3 Railway CLI Commands
```bash
# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open

# SSH into container (debugging)
railway shell
```

### 4.4 Check Resource Limits
**Railway Free Tier:**
- $5 free credits per month
- Shared CPU and RAM
- No automatic sleep (runs continuously)
- 100GB bandwidth

**For Production Use:**
- Add payment method for usage beyond free tier
- Monitor costs in Railway dashboard
- Typical Soliloquy usage: ~$2-5/month (including Railway + API costs)

---

## Troubleshooting

### Common Issues

#### ❌ Bot Not Starting
**Symptoms**: No logs, deployment fails
**Solutions**:
```bash
# Check logs
railway logs

# Verify environment variables
railway variables

# Check Procfile
cat Procfile
# Should contain: worker: python bot.py
```

#### ❌ API Key Errors
**Symptoms**: "Missing API keys in environment variables"
**Solutions**:
```bash
# List current variables
railway variables

# Re-set variables with exact names (case-sensitive!)
railway variables --set TELEGRAM_TOKEN="..."
railway variables --set OPENAI_API_KEY="..."
railway variables --set GEMINI_API_KEY="..."

# Redeploy
railway up
```

#### ❌ Image Generation Failing
**Symptoms**: "GEMINI_API_KEY not found" or "ResourceExhausted"
**Solutions**:
- Verify Gemini API key is set: `railway variables | grep GEMINI`
- Check key is valid (starts with `AIzaSy`)
- Verify you haven't exceeded free tier quota (1500 requests/day)
- Get new key from [AI Studio](https://aistudio.google.com/app/apikey)

#### ❌ Voice Transcription Not Working
**Symptoms**: Voice messages fail to transcribe
**Solutions**:
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI account has credits
- Review logs for specific Whisper errors
- Test API key locally: `python -c "from openai import OpenAI; print(OpenAI().models.list())"`

#### ❌ Import Errors
**Symptoms**: `ModuleNotFoundError`
**Solutions**:
```bash
# Check requirements.txt includes all dependencies
cat requirements.txt

# Should include:
# python-telegram-bot==20.7
# openai==1.52.0
# python-dotenv==1.0.0
# google-genai>=1.46.0
# pillow>=10.0.0

# Force rebuild
git commit --allow-empty -m "Force Railway rebuild"
git push origin main
```

#### ❌ Conversation History Not Saving
**Symptoms**: Bot forgets previous messages
**Solutions**:
- Railway provides persistent storage by default
- Check logs for permission errors
- Verify `conversations/` directory is created on startup

---

## Performance Optimization

### Reduce API Costs
1. **Limit conversation history**: Already set to 20 messages
2. **Monitor token usage**: Check OpenAI dashboard regularly
3. **Cache responses**: Consider caching common patterns (future enhancement)

### Improve Response Time
1. **Use Railway regions**: Deploy to region closest to users
2. **Optimize Gemini calls**: Images generate in ~10-15 seconds (expected)
3. **Pre-warm API connections**: Already implemented in startup

---

## Security Best Practices

### 1. Protect API Keys
- ✅ **Never commit** API keys to Git
- ✅ Use environment variables only
- ✅ Add `.env` to `.gitignore` (already configured)

### 2. Rotate Keys Periodically
```bash
# Generate new keys from providers
# Update in Railway
railway variables --set TELEGRAM_TOKEN="new_token"
railway variables --set OPENAI_API_KEY="new_key"

# Railway auto-redeploys on variable change
```

### 3. Monitor Bot Usage
- Set up OpenAI usage alerts
- Check Telegram bot analytics
- Review Railway logs for unusual activity

### 4. Rate Limiting
- OpenAI: Built-in rate limits
- Gemini: 15 requests/minute (handled by API)
- Telegram: 30 messages/second (no issue for typical usage)

---

## Scaling Considerations

### For Higher Traffic:
1. **Upgrade Railway plan**: More CPU/RAM for concurrent users
2. **Database integration**: Store neologisms in PostgreSQL (future enhancement)
3. **Caching layer**: Redis for conversation history (future enhancement)
4. **Webhook mode**: More efficient than polling for high-volume bots

### Production Checklist:
- ✅ All environment variables configured
- ✅ Bot responding to `/start` command
- ✅ Logs showing successful startup
- ✅ API keys working (Telegram, OpenAI, Gemini)
- ✅ Image generation tested
- ✅ Voice transcription tested
- ✅ Photo upload tested
- ✅ Error handling verified
- ✅ Resource usage monitored

---

## Cost Estimates

### Monthly Costs (Typical Usage - 100 neologisms/month):
- **Railway**: $0-2 (free tier covers most usage)
- **OpenAI**: $5-10 (GPT-4o-mini + Whisper)
- **Gemini**: $0 (free tier: 1500 requests/day)
- **Telegram**: $0 (free)

**Total**: ~$5-12/month

### High Usage (1000 neologisms/month):
- **Railway**: $5-10
- **OpenAI**: $50-100
- **Gemini**: $0-20 (may exceed free tier)
- **Telegram**: $0

**Total**: ~$55-130/month

---

## Support and Resources

### Railway Documentation
- [Railway Docs](https://docs.railway.app)
- [Railway CLI Guide](https://docs.railway.app/develop/cli)
- [Railway Troubleshooting](https://docs.railway.app/troubleshoot/fixing-common-errors)

### API Documentation
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Soliloquy Resources
- **Repository**: [github.com/korokseedling/soliloquy](https://github.com/korokseedling/soliloquy)
- **README**: Comprehensive usage guide
- **CLAUDE.md**: Detailed implementation documentation

### Getting Help
- Check `soliloquy_bot.log` for detailed error information
- Review Railway logs for deployment issues
- Monitor API status pages for outages
- Submit issues on GitHub repository

---

## Updating Soliloquy

When new versions are released:

```bash
# Pull latest changes
git pull origin main

# Test locally
python bot.py

# Push to Railway
git push origin main

# Railway auto-deploys new version
```

---

**Your Soliloquy bot is now live, ready to name the unnamed! 💭✨**

*A voice from within, running in the cloud, waiting for feelings without words.*
