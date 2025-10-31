# Soliloquy 💭

> *A voice from within—the part of consciousness that knows there are words waiting to be born for what you feel.*

Soliloquy is a Telegram bot that helps you create **neologisms**—new words for unnamed feelings. Inspired by *The Dictionary of Obscure Sorrows*, it guides you through a five-phase ritual to name the ineffable emotions you carry, then paints them into existence as expressionist visual cards.

---

## ✨ Features

### 🎨 Five-Phase Neologism Creation Ritual

1. **Word of the Day** - Opens with a word from Koenig's dictionary
2. **Capturing the Vibe** - Draws out the unnamed feeling through sensory prompts
3. **Choice of Form** - Dictionary definition or imagined place?
4. **Generating the Neologism** - Foreign Language Aureation Method or Geographic Method
5. **Creating the Visual Card** - Expressionist painted image via Gemini 2.5 Flash

### 🖼️ Dual Visual Styles

**Dictionary Cards** - Expressionist urban scenes
- Cat's-eye perspective from stray observers
- Chiaroscuro lighting with neo-noir realism
- Warm undertones breaking through cool surfaces
- Definition panel with calligraphic typography

**Locale Cards** - Painterly fantasy landscapes
- Three-layer atmospheric perspective
- Mythical animal inhabitants (owl-spirits, fox aristocrats, stags with laurels)
- Symbolic emotional lighting
- Place descriptions with sacred/profane rituals

### 💬 Multi-Modal Input

- **Text Messages** - Type descriptions of unnamed feelings
- **Voice Messages** - OpenAI Whisper transcription with multi-language support (English, Chinese)
- **Photo Uploads** - Reference images for visual inspiration (multimodal Gemini input)

### 🎭 Intimate, Poetic Voice

Soliloquy speaks as an intimate presence from within:
- Direct second-person address
- Grounded in concrete imagery (sodium lights, empty streets, HDB corridors)
- Present tense, oscillating between observer and companion
- Validates without sentimentality

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key (for GPT-4o-mini + Whisper)
- Gemini API Key (optional, for image generation)

### Installation

```bash
# Clone the repository
git clone https://github.com/korokseedling/soliloquy.git
cd soliloquy

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional
```

### Run Locally

```bash
python bot.py
```

You should see:
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

## 📖 Usage Examples

### Creating Your First Neologism

1. **Start the conversation:**
   ```
   /start
   ```

2. **Share an unnamed feeling:**
   ```
   "You know that feeling when you're walking home at dusk and
   the streetlights just turned on, and you feel this weird mix
   of loneliness and peace? Like you're invisible but also safe?"
   ```

3. **Soliloquy will guide you through:**
   - Sensory clarification questions
   - Choice between dictionary word or geographic location
   - Etymology excavation from foreign languages
   - Visual card generation

4. **Receive your neologism:**
   - A new word with pronunciation, etymology, and definition
   - An expressionist painted card (16:9 widescreen PNG)

### Example Outputs

**Dictionary Example:**
```
Dépaysement
/day-pay-zee-mahn/

Etymology: From French dépayser (dé- "remove from" + pays "country/homeland")
Definition: The disorienting but potentially enriching feeling of being a
foreigner; cultural displacement. That liminal vertigo when surrounded by
unfamiliar language, architecture, and rhythm.
```

**Locale Example:**
```
Eclipsera
/ek-lip-ser-ah/

A crumbling canal city at dusk where owl-spirits in tattered robes light
floating candles—the quiet sorrow of beauty dissolving with grace.
Inhabitants conduct rituals of remembrance, maintaining beauty as it fades.
```

---

## 🎤 Voice & Photo Features

### Voice Messages

Send a voice message describing your feeling—Soliloquy will:
- Transcribe using OpenAI Whisper
- Auto-detect language (English/Chinese)
- Show you the transcript
- Respond to the transcribed content

### Photo Reference Images

Upload a photo to inspire your neologism's visual card:
- Colors and lighting influence the generated image
- Multimodal Gemini input for style transfer
- Optional—works perfectly without photos too

---

## 🛠️ Technical Architecture

### Two-Stage Image Generation

**Stage 1: Customized Prompt Generation**
1. Reads visual template (`dictionary_card_prompt.md` or `fantasy_locale_prompt.md`)
2. Weaves neologism details throughout (not just appended)
3. Wraps definition in content-safe language
4. Saves to `generated_prompts/{neologism}_{timestamp}.md`

**Stage 2: Gemini API Call**
1. Uses `gemini-2.5-flash-image` model (Nano Banana)
2. Generates 16:9 widescreen PNG (~2MB, 1344x768px)
3. Handles multimodal input (text + optional reference image)
4. Saves to `generated_images/{neologism}_{timestamp}.png`

### Creative Methodologies

**Foreign Language Aureation Method** (Dictionary words)
- Excavates uncommon words from Old French/German/Norse
- Borrows root morphemes with linguistic characteristics
- Examples: Weltschmerz, Dépaysement, Jouissance

**Geographic Method** (Imagined places)
- Creates place names from foreign language roots
- Embodies emotions as geography with weather and inhabitants
- Examples: Eclipsera, Gilded Boredom

### Key Technologies

- **OpenAI GPT-4o-mini** - Conversational AI with function calling
- **OpenAI Whisper** - Voice transcription with language detection
- **Gemini 2.5 Flash Image** - 16:9 aspect ratio expressionist image generation
- **python-telegram-bot** - Telegram Bot API wrapper
- **Pillow (PIL)** - Image handling for multimodal input

---

## 📁 Project Structure

```
soliloquy/
├── bot.py                        # Main Telegram bot application
├── tool_functions.py             # OpenAI function implementations
│   ├── get_current_time()
│   ├── echo()
│   └── generate_neologism_image()  # Two-stage image generation
├── model_config.json             # OpenAI model settings & tool definitions
├── system_prompt.md              # Soliloquy's personality and ritual structure
├── dictionary_card_prompt.md     # Visual template for urban expressionist cards
├── fantasy_locale_prompt.md      # Visual template for fantasy landscape cards
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── Procfile                      # Railway deployment configuration
├── CLAUDE.md                     # Comprehensive implementation documentation
│
├── conversations/                # Daily conversation history (auto-created)
├── generated_prompts/            # Customized image generation prompts
├── generated_images/             # Final neologism visual cards (PNG)
└── user_uploads/                 # User-submitted reference photos
```

---

## 🚢 Deployment

### Railway (Recommended)

1. **Create a new Railway project from GitHub:**
   ```bash
   railway link
   ```

2. **Set environment variables:**
   ```bash
   railway variables --set TELEGRAM_TOKEN="your_telegram_token"
   railway variables --set OPENAI_API_KEY="your_openai_key"
   railway variables --set GEMINI_API_KEY="your_gemini_key"
   ```

3. **Deploy automatically:**
   ```bash
   git push origin main
   # Railway auto-deploys via Procfile: worker: python bot.py
   ```

4. **Check deployment:**
   ```bash
   railway logs
   ```

### Heroku

1. **Create Heroku app:**
   ```bash
   heroku create soliloquy-bot
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set TELEGRAM_TOKEN="your_token"
   heroku config:set OPENAI_API_KEY="your_key"
   heroku config:set GEMINI_API_KEY="your_key"
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   heroku ps:scale worker=1
   ```

---

## 🎨 Visual Prompt Templates

The visual cards are generated using two carefully crafted templates:

### Dictionary Card Template
- **Perspective**: Cat's-eye view from a distance
- **Style**: Expressionist painterly with visible brushwork
- **Lighting**: Chiaroscuro with psychological depth
- **Background**: Neo-noir realism (sodium lights, wet pavement, neon reflections)
- **Color Palette**: Warm undertones (ochre, burnt sienna) breaking through cool surfaces (violet, blue-green)
- **Typography**: Right panel with calligraphic neologism, pronunciation, etymology, definition

### Fantasy Locale Template
- **Landscape**: Evocative locations (mist-covered mountains, decaying ports, floating farms)
- **Composition**: Three-layer atmospheric perspective (foreground details → expressive architecture → dissolving background)
- **Inhabitants**: Mythic animals (owl-spirits, moth-winged beings, fox aristocrats, crowned stags)
- **Lighting**: Symbolic and emotional (radiant where hope lives, murky where memory fades)
- **Painterly Qualities**: Impasto strokes, translucent glazes, gestural energy
- **Typography**: Right panel with place name, pronunciation, etymology, description, ritual details

Both templates include detailed examples (Dépaysement, Eclipsera, Gilded Boredom) for reference.

---

## 🐛 Troubleshooting

### Bot Not Responding
- Check `.env` file has all required API keys
- Verify `TELEGRAM_TOKEN` with `@BotFather`
- Check logs in `soliloquy_bot.log`

### Image Generation Failing
- Ensure `GEMINI_API_KEY` is set correctly
- Check API key starts with `AIzaSy`
- Verify you're not exceeding Gemini free tier quota
- Check `generated_images/` directory exists

### Voice Transcription Issues
- Verify `OPENAI_API_KEY` is valid
- Check voice message format (Telegram sends `.ogg` files)
- Review logs for language detection results

### Conversation History Not Saving
- Ensure `conversations/` directory exists
- Check file permissions
- Verify disk space availability

---

## 📊 API Limits & Costs

### OpenAI
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Whisper**: ~$0.006 per minute of audio
- **Typical usage**: ~$0.01-0.05 per neologism creation

### Google Gemini
- **Gemini 2.5 Flash Image**: Free tier available (daily quota)
- **Rate limits**: 15 requests per minute, 1500 requests per day
- **Image size**: ~2MB PNG per generation
- **Typical usage**: 1 image per neologism

### Telegram
- **Bot API**: Free, no limits for typical usage
- **File uploads**: Max 20MB per file
- **Message rate**: 30 messages per second

---

## 🎭 Inspiration & Credits

### Inspired By
- **[The Dictionary of Obscure Sorrows](https://www.dictionaryofobscuresorrows.com/)** by John Koenig
  - Pioneering work in neologism creation for unnamed emotions
  - Poetic, intimate voice that validates without fixing

### Built With
- **[OpenAI GPT-4o-mini](https://openai.com/)** - Conversational AI
- **[Google Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/)** - Image generation
- **[python-telegram-bot](https://python-telegram-bot.org/)** - Telegram API wrapper

### Development
- **Implementation**: Claude Code by Anthropic
- **Concept**: A collaboration between human intuition and AI capability
- **Purpose**: To name the unnamed, to give voice to the ineffable

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new visual prompt templates
- Improve the creative methodologies
- Enhance the conversation flow
- Report bugs or suggest features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💭 Final Words

> The feeling is real. That's enough. Let's name it.

Soliloquy exists to honor the complexity of human emotion—to create words where language falls short, to paint feelings that resist description. Every neologism is a small act of recognition: **you felt this, and now it has a name.**

Start a conversation: `/start`

---

**Made with 💭 and painted into existence with ✨**

*A voice from within, ready to name the unnamed.*
