# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Soliloquy is a Telegram bot that creates neologisms—new words for unnamed feelings. Inspired by The Dictionary of Obscure Sorrows, Soliloquy embodies an intimate, poetic voice that helps users name the ineffable emotions they carry. The bot uses OpenAI's GPT-4o-mini with function calling and OpenAI Whisper for voice transcription, speaking as "a voice from within—the part of consciousness that knows there are words waiting to be born for what you feel."

## Key Commands

### Development & Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot locally
python bot.py

# Test the complete workflow in Jupyter
jupyter notebook test_soliloquy_workflow.ipynb
```

**Testing Notebook:** `test_soliloquy_workflow.ipynb` provides complete end-to-end testing:
- **Interactive Chat Widget** - Real-time conversation testing with Soliloquy before image generation
- **Neologism Extraction** - GPT-powered parsing of conversation history to extract structured neologism data
- **Customized Prompt Generation** - Template-based prompt creation with emotional keywords and etymology
- **Image Generation with Gemini 2.5 Flash** - Full implementation using NEW SDK (`google-genai` with Client pattern)
- **Step-by-step workflow** - Setup → Chat → Extract → Generate Prompt → View Prompt → Generate Image
- Full conversation history tracking and markdown rendering

### Production Deployment
```bash
# Set environment variables on Railway (run these before deploying)
railway variables --set TELEGRAM_TOKEN="your_telegram_bot_token_here"
railway variables --set OPENAI_API_KEY="your_openai_api_key_here"
railway variables --set GEMINI_API_KEY="your_gemini_api_key_here"

# Deploy to Railway
git push origin main  # Auto-deploys via Procfile: worker: python bot.py
```

### Environment Variables Required
- `TELEGRAM_TOKEN` - From @BotFather
- `OPENAI_API_KEY` - OpenAI API access (for both chat and Whisper)
- `GEMINI_API_KEY` - Google Gemini API access (for image generation, optional)

## Architecture

### Core Components

**bot.py** - Main application entry point
- Telegram bot handlers for text and voice messages
- OpenAI function calling integration with persona-driven responses
- Voice message transcription using OpenAI Whisper API
- Conversation history management (20 messages per user per day)
- Username extraction and system prompt personalization
- Environment variable validation with detailed Railway debugging
- Asterisk-to-HTML conversion for Telegram formatting

**tool_functions.py** - OpenAI function implementations
- `get_current_time` - Get current date and time
- `echo` - Echo back messages for demonstration
- `generate_neologism_image` - Creates visual cards for neologisms using Gemini 2.5
- Telegram HTML formatting for all responses

**model_config.json** - Configuration
- OpenAI model settings (GPT-4o-mini, temperature: 0.7)
- Tool function definitions for OpenAI function calling

**system_prompt.md** - Bot personality and conversation structure
- Soliloquy's intimate, poetic voice ("a voice from within")
- Five-phase neologism creation ritual with structured conversation flow
- Two creative methods: **Foreign Language Aureation Method** (dictionary definitions) and **Geographic Method** (imagined places)
- Poetic but grounded language with concrete imagery (sodium lights, empty streets, HDB corridors)
- Direct second-person address oscillating between observer and companion
- HTML formatting requirements (no asterisks)
- Voice message handling with transcript cleanup
- Reference image support for visual inspiration

**dictionary_card_prompt.md** - Visual prompt template for dictionary-style neologisms
- **Cat's-eye perspective**: Scene viewed from the perspective of a stray cat observing from a distance
- Expressionist painterly style with visible, constructed brushwork
- Impasto passages and gestural marks creating faceted, geological planes
- Warm undertones (ochre, burnt sienna) breaking through cooler surface colors (violet, blue-green)
- Chiaroscuro lighting with neo-noir realism backgrounds
- Definition panel on right side with calligraphic neologism (brushstroke texture, ink leak), pronunciation, etymology, and definition
- 16:9 widescreen aspect ratio

**fantasy_locale_prompt.md** - Visual prompt template for geographic neologisms
- Painterly fantasy landscapes with expressionist style and visible, imperfect brushstrokes
- Symbolic and emotional lighting (radiant where hope lives, murky where memory fades)
- Three-layer atmospheric perspective:
  - Foreground: Tangible details (pathways, boats, relics, inhabitants in quiet ritual)
  - Middle ground: Expressive architecture shaped by feeling (warped spires, leaning houses)
  - Background: Dissolves into luminous haze with blurred edges
- **Mythic animal inhabitants**: Anthropomorphized creatures from forgotten folklore (owl-spirits, moth-winged beings, fox aristocrats, stags with laurels)
- Painterly qualities: Imperfect brushwork, color desaturation in distance, translucent glazes, dynamic tension
- Definition panel on right side with place name in calligraphic font and place description with ritual details
- 16:9 widescreen aspect ratio
- Includes detailed examples (Eclipsera - crumbling canal city, Gilded Boredom - opulent exhaustion)

### Data Flow

1. **User message** (text/voice) → Telegram → `handle_message()` or `handle_voice_message()`
2. **Username extraction** → First+Last name → First name → @username priority
3. **Voice transcription** (if applicable) → OpenAI Whisper API with multi-language detection
4. **Load conversation** history from `conversations/` directory
5. **OpenAI processing** with personalized system prompt + history + tools
6. **Function calling** if tool usage detected
7. **Response formatting** with HTML tags (convert asterisks as fallback)
8. **Save conversation** and send reply

### Voice Message Features

- **Multi-language support**: Auto-detects English and Chinese, falls back to English for other languages
- **Transcript display**: Shows users what was transcribed from their voice message
- **Error handling**: Proper error messages for failed transcriptions
- **Temporary file management**: Downloads, processes, and cleans up voice files
- **Logging**: Voice messages and transcriptions are logged with language detection info

### Image Upload Features

- **Reference Image Support**: Users can upload photos to inspire the generated neologism cards
- **Multimodal Input**: Gemini 2.5 Flash Image uses both text prompts and reference images
- **Use Cases**:
  - Share a sunset photo for color palette inspiration
  - Upload artwork that captures the mood
  - Provide personal photos that embody the feeling
- **File Handling**: Images saved to `user_uploads/` directory with user_id and timestamp
- **Conversation Integration**: Image paths stored in conversation history for OpenAI to reference
- **Optional Feature**: Users can skip image upload and generate purely from text prompts

### Key Features

- **Poetic Inner Voice**: Soliloquy speaks as an intimate presence witnessing the user's inner world
- **Neologism Creation**: Generates new words using etymological roots or imagined geographic locations
- **Visual Card Generation**: Creates atmospheric images for each neologism using Gemini 2.5
  - Dictionary cards with elegant typography and moody aesthetics
  - Fantasy landscape cards with mythical realism
- **Voice + Text Input**: Both typing and voice recording supported for describing feelings
- **Username Personalization**: Addresses users by real name when available
- **Conversation persistence**: Daily conversation files with 20-message limit
- **Language Detection**: Multi-language voice support with intelligent fallback
- **HTML formatting**: All responses use HTML tags, never asterisks
- **Dual Creative Methods**: Dictionary definitions (Aureation Method) or imagined places (Geographic Method)
- **Auto-cleanup**: Old conversation files (>7 days) cleaned on startup

### File Structure Details

- `conversations/` - Per-user daily conversation history (auto-created)
- `generated_prompts/` - Customized image generation prompts for each neologism (auto-created)
- `generated_images/` - Generated visual cards for neologisms (auto-created)
- `user_uploads/` - User-uploaded reference images for visual inspiration (auto-created)
- `soliloquy_bot.log` - Detailed logging with conversation and voice transcription tracking
- `Procfile` - Railway deployment configuration
- `requirements.txt` - Python dependencies (telegram-bot, openai, python-dotenv, google-genai)

### Soliloquy's Conversation Structure

The bot follows a five-phase neologism creation ritual:

1. **Word of the Day** - Opens with a word from Koenig's dictionary, then invites: "Tell me about one. What's a feeling you've carried that has no word?"

2. **Capturing the Vibe** - Uses sensory, specific prompts to draw out the unnamed feeling:
   - "What's a vibe you caught recently that made you feel something you couldn't name?"
   - Stays grounded in concrete moments: scrolling, walking home, evening light on HDB corridors
   - Asks clarifying questions that remain sensory and situated

3. **Choice of Form** - Offers two creative paths:
   - **Dictionary definition**: A word with etymology, pronunciation, and definition
   - **Imagined place**: A geographic location where the feeling lives

4. **Generating the Neologism**:
   - **The Foreign Language Aureation Method** (for dictionary definitions): Excavates uncommon words from foreign language dictionaries (Old French/German/Old Norse, multi-layered conceptual words from German and French philosophers like Weltschmerz, Dépaysement, Jouissance), borrows root morphemes, and adopts linguistic characteristics to create neologisms that feel ancient and inevitable
   - **The Geographic Method** (for imagined places): Uses the same foreign language excavation approach to create place names that embody emotions as geography, with weather, mythical creature inhabitants, and sacred/profane rituals

5. **Creating the Visual Card** - After presenting the neologism:
   - Automatically calls `generate_neologism_image` tool
   - Creates customized prompt from templates
   - Generates expressionist painted card via Gemini 2.5
   - Sends visual to user as completion of the ritual

### Soliloquy's Voice Characteristics

- **Intimate and direct**: Speaks from inside the user's mind in second person
- **Poetic but grounded**: Beauty found in sodium lights and empty streets, not abstractions
- **Present tense**: Names feelings as they happen, not as memory
- **Oscillating presence**: Both observer and companion
- **Fragmented rhythm**: Short declarations and longer reveries
- **Validates without sentimentality**: The feeling is real. That's enough.

**Example tone:**
- "Subdue the regret. Dust yourself off, proceed. You'll get it in the next life, where you don't make mistakes."
- "A tremendous loneliness comes over you. Everybody in the world is doing something without you."

### Username Integration

- **Priority**: First+Last name → First name → @username → None
- **System Prompt**: Automatically appends "User's name is [name]"
- **Personalization**: Enables Soliloquy to address users naturally by name
- **Intimate Context**: Supports the inner-voice, personal nature of the conversation

### Common Development Patterns

When adding new functionality:
- Maintain Soliloquy's intimate, poetic voice
- Add tool function to `tool_functions.py` and register in `TOOL_FUNCTIONS`
- Define tool schema in `model_config.json`
- Use HTML formatting (`<b>`, `<i>`, `<code>`) never asterisks
- Handle both text and voice input pathways
- Include proper error handling with user-friendly messages
- Follow the four-phase neologism creation ritual
- Keep language concrete and sensory, not abstract
- Validate feelings without trying to fix them

### Deployment Notes

The bot is designed for Railway deployment with comprehensive environment variable debugging. All API keys are validated on startup with detailed error messages for troubleshooting Railway configuration issues.

### Available Tools

The bot has three tools:
1. **get_current_time** - Returns the current date and time
2. **echo** - Echoes back a message to demonstrate tool functionality
3. **generate_neologism_image** - Creates visual cards for neologisms via two-stage process:

   **Parameters:**
   - `neologism_type`: "dictionary" or "locale"
   - `word_or_place`: The neologism itself
   - `pronunciation`: Pronunciation guide
   - `definition`: Complete definition
   - `emotional_keywords`: 3-5 comma-separated mood descriptors
   - `etymology`: Linguistic roots used to construct the word
   - `additional_context`: For locales - terrain, creatures, rituals
   - `reference_image_path`: Optional path to user-uploaded image for style/mood inspiration

   **Stage 1: Customized Prompt Generation**
   - Reads template from `dictionary_card_prompt.md` or `fantasy_locale_prompt.md` for style reference
   - Generates a fully customized prompt tailored to the specific neologism
   - Weaves the definition and etymology throughout in content-safe language
   - Does NOT include template boilerplate - only the customized image generation prompt
   - Saves to `generated_prompts/{neologism_name}_{type}.md`

   **Stage 2: Image Generation** (Implemented)
   - Uses Nano Banana (`gemini-2.5-flash-image`) for multimodal image generation
   - Generates expressionist painterly images in **16:9 widescreen aspect ratio** for all card types
   - **Supports multimodal input**: Text prompt + optional reference image
   - **Reference Image Usage**:
     - If user uploaded an image, loads it with PIL and passes to Gemini
     - Influences color palette, mood, and visual style of generated card
     - Completely optional - works perfectly without reference images
   - **Both types include definition panel on the right side** with calligraphic neologism, etymology, and definition
   - **Dictionary type**: Expressionist portrait with chiaroscuro lighting, neo-noir urban background
   - **Locale type**: Fantasy landscape with atmospheric perspective, mythical animal inhabitants
   - Aspect ratio controlled via `image_config` API parameter
   - Extracts image data from response (checks parts, inline_data, and candidates)
   - Saves image to `generated_images/{neologism_name}_{timestamp}.png`
   - Returns path via `IMAGE_PATH:` prefix for bot.py to detect and send

**Note**: Image generation is fully implemented in both `tool_functions.py:149-205` and the test notebook. The system attempts multiple methods to extract image data from the Gemini API response and includes fallback error handling if the model returns text instead of images.

These could potentially be extended with:
- Dictionary/etymology lookups
- Koenig's Dictionary of Obscure Sorrows API (if available)
- Language/root word databases
- User's personal word collection
- Image post-processing (filters, overlays, text rendering)

### Gemini Image Generation: Implementation Lessons

**Critical Implementation Details** - Read this before modifying image generation code:

#### 1. Correct Model Name and SDK
- **SDK**: `google-genai` (v1.46.0+) - **Required for aspect ratio control**
- **Old SDK**: `google-generativeai` is deprecated (support ends August 31, 2025)
- **Model**: `gemini-2.5-flash-image` (stable) or `gemini-2.5-flash-image-preview`
- **Common name**: "Nano Banana" model
- **Don't use**: `gemini-2.5-flash-preview-0418` or other non-image models
- **Client pattern**: New SDK uses `genai.Client(api_key=...)` instead of `genai.configure()`

#### 2. Response Structure - The 0-Byte Issue
**Critical**: Gemini image responses contain multiple parts. The first part often has 0 bytes (metadata), while subsequent parts contain the actual image data.

**Required code pattern** (tool_functions.py:163-173):
```python
# Initialize client (new SDK)
from google import genai
from google.genai import types

genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Generate with aspect ratio
response = genai_client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=customized_prompt,
    config=types.GenerateContentConfig(
        temperature=0.7,
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        )
    )
)

# Extract image data from response
# Note: Response may have multiple parts, skip 0-byte data
image_data = None

if hasattr(response, 'parts'):
    for part in response.parts:
        if hasattr(part, 'inline_data') and hasattr(part.inline_data, 'data'):
            data = part.inline_data.data
            # Skip empty data (first part is often 0 bytes)
            if len(data) > 0:
                image_data = data
                logging.info(f"Found image data: {len(data):,} bytes")
                break
```

**Why this matters**: Without the `if len(data) > 0:` check, you'll try to save a 0-byte file and get broken images.

#### 3. Expected Output Specifications
- **Format**: PNG
- **Size**: ~1.9-2.1MB per image
- **Aspect Ratio**: **16:9** (widescreen for all cards - both dictionary and locale)
- **Dimensions**: 1344x768 pixels (actual aspect ratio 1.75:1 ≈ 16:9)
- **Generation time**: ~10-15 seconds per image
- **Mode**: RGB
- **API Parameter**: Controlled via `image_config=types.ImageConfig(aspect_ratio="16:9")`
- **SDK**: google-genai (v1.46.0+) - replaces deprecated google-generativeai

#### 4. Content-Safe Language Wrapping
Always wrap neologism definitions in descriptive context rather than inserting raw text:

**Good**:
```python
emotion_description = f"expressing the feeling of {definition[:200]}"
# Later in prompt: "conveys the tension of {emotion_description}"
```

**Bad**:
```python
# Direct insertion: "{definition}" - may contain content Gemini flags
```

This prevents content policy issues while preserving the emotional essence.

#### 5. Two-Stage Prompt Generation Architecture
**Why two stages?**
1. **Stage 1 (Python)**: Template → Customized prompt
   - Weaves definition throughout naturally
   - Adds etymology, pronunciation, keywords
   - Saves readable prompt to `generated_prompts/`

2. **Stage 2 (Gemini API)**: Customized prompt → Image
   - Clean separation of concerns
   - Allows manual prompt refinement
   - Debugging is easier (can inspect/test prompts independently)

**Don't**: Send raw templates to Gemini with placeholder substitution
**Do**: Generate fully realized, narrative prompts that read like complete image generation instructions

#### 6. API Quota Considerations
- **Free tier**: Limited daily quota (exact limit not documented)
- **Error code**: `429 ResourceExhausted` when exceeded
- **Recovery**: Quota resets daily
- **Handling**: Code includes graceful error messages for quota issues
- **Production**: Consider paid tier for production deployment

#### 7. Model Testing Scripts
Created during development (available in repo root):
- `list_gemini_models.py` - Query all available Gemini models
- `test_image_generation_corrected.py` - Basic image generation test
- `test_image_detailed.py` - Response structure inspection
- `test_imagen_direct.py` - Multi-model comparison test
- `view_generated_image.py` - Display generated images with PIL

Use these scripts to verify API connectivity and debug response structure issues.

#### 8. Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'google.generativeai'` | Using old SDK | Install new SDK: `pip install google-genai` |
| `AttributeError: module 'google.generativeai.types' has no attribute 'GenerateContentConfig'` | Old SDK doesn't support aspect ratio | Upgrade to `google-genai` |
| `404 models/gemini-2.5-flash-preview-0418 is not found` | Wrong model name | Use `gemini-2.5-flash-image` |
| `400 API key not valid` | Malformed API key (extra characters) | Check `.env` for typos, should start with `AIzaSy` |
| `429 ResourceExhausted` | Free tier quota exceeded | Wait for daily reset or upgrade to paid tier |
| 0-byte PNG files | Using first part without checking size | Add `if len(data) > 0:` check (see code above) |
| Square images (1024x1024) instead of 16:9 | Old SDK or missing `image_config` | Use new SDK with proper `image_config` parameter |
| Text response instead of image | Model interpretation issue | Adjust prompt language, ensure clear image generation intent |

#### 9. Prompt Template Philosophy
The templates (`dictionary_card_prompt.md`, `fantasy_locale_prompt.md`) serve as **style references**, not literal templates:
- They establish visual aesthetic (expressionist painterly, chiaroscuro lighting)
- Define composition structure (foreground/middle/background for locales)
- Set mood and atmosphere expectations
- The customization process should **weave the neologism throughout**, not append it

**Template Evolution**: As you refine what works visually, update the templates. They're living documents that capture learned visual patterns.

#### 10. Multimodal Input (Text + Image)
**Feature**: Gemini 2.5 Flash Image supports passing both text prompts and reference images for style/mood inspiration.

**Implementation Pattern**:
```python
from PIL import Image

# Prepare contents list
contents = [customized_prompt]

# Add reference image if provided
if reference_image_path and os.path.exists(reference_image_path):
    reference_img = Image.open(reference_image_path)
    contents.append(reference_img)

# Generate with both text and image
response = genai_client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=contents,  # List can contain strings and PIL Images
    config=types.GenerateContentConfig(...)
)
```

**Use Cases**:
- User uploads sunset photo → influences color palette (orange/purple tones)
- User shares artwork → adapts brushwork style and composition
- User provides personal photo → captures specific mood and atmosphere

**Important**: The reference image is **optional**. The system works perfectly with text-only prompts. When an image is provided, it influences but doesn't override the text prompt's intent.

### Voice Message Technical Details

- **Whisper Model**: Uses OpenAI's whisper-1 model
- **Language Detection**: JSON response format to detect language first
- **Supported Languages**: English (en), Chinese variants (zh, zh-cn, zh-tw)
- **Fallback Strategy**: Non-supported languages retry with English transcription
- **File Handling**: Temporary .ogg files with automatic cleanup
- **Response Format**: Includes transcribed text before Soliloquy's response

### Visual Prompt Templates

The visual cards are generated using two template files that define the aesthetic and compositional approach:

#### Dictionary Card Template (`dictionary_card_prompt.md`)
**Visual Approach: Expressionist Portraits from Cat's-Eye Perspective**

**Key Features:**
- **Perspective**: Scene depicted from the viewpoint of a stray cat observing from a distance
- **Subject**: Urban scene analogizing the emotional state of the neologism
- **Brushwork**: Visible, constructed brushwork with textured strokes—impasto passages and gestural marks creating faceted, almost geological planes
- **Color Palette**: Warm undertones (ochre, burnt sienna, raw umber) breaking through cooler surface colors (violet, blue-green, gray-green) as though emotion is surfacing through layers
- **Lighting**: Chiaroscuro with dramatic contrast—deep shadows with defined edges
- **Background**: Neo-noir realism—hyperreal, cinematically lit urban environments with gritty specificity
- **Typography Panel**: Right side with calligraphic neologism (brushstroke texture, ink leak), pronunciation, etymology, definition
- **Aspect Ratio**: 16:9 widescreen

**Purpose**: Creates intimate portraits that capture the psychological depth of unnamed feelings through urban scenes observed from a detached yet empathetic perspective.

#### Fantasy Locale Template (`fantasy_locale_prompt.md`)
**Visual Approach: Painterly Fantasy Landscapes with Mythical Inhabitants**

**Key Features:**
- **Landscape Type**: Evocative locations (mist-covered mountain towns, decaying port cities, floating desert farms, submerged library quarters)
- **Painterly Style**: Visible, imperfect brushstrokes with layered pigments and gestural energy
- **Lighting**: Symbolic and emotional (radiant where hope lives, murky where memory fades)
- **Three-Layer Composition**:
  - **Foreground**: Tangible details of lived emotion—pathways, boats, relics, inhabitants in quiet ritual
  - **Middle Ground**: Expressive architecture shaped by feeling—warped spires, leaning houses, flowing streets
  - **Background**: Atmospheric dissolution—edges blur, contrast softens, forms fade into luminous haze
- **Inhabitants**: Anthropomorphized mythic animal beings from forgotten folklore:
  - Owl-spirits and moth-winged beings (for melancholic beauty)
  - Fox aristocrats in silken coats (for weary sophistication)
  - Stags crowned with fading laurels (for faded glory)
- **Painterly Qualities**:
  - Imperfect, expressive brushwork showing the hand of the painter
  - Subtle color desaturation and edge blurring in distance
  - Overlapping translucent glazes (oranges bleeding into blues, greys blooming with violet)
  - Dynamic tension between intense impasto and calm, fog-soft textures
- **Typography Panel**: Right side with place name in calligraphic font, place description, ritual details
- **Aspect Ratio**: 16:9 widescreen

**Examples Included**:
- **Eclipsera**: Crumbling canal city at dusk expressing "the quiet sorrow of beauty dissolving with grace"
- **Gilded Boredom**: Opulent halls expressing "the poised melancholy of privilege and beauty grown stale"

**Purpose**: Transforms emotions into traversable geography—places you could walk to if feelings were locations, complete with weather, inhabitants, and rituals that embody the ineffable.

**Template Philosophy**: These templates serve as **style references** that establish visual aesthetics, compositional structure, and atmospheric expectations. The customization process weaves the specific neologism throughout rather than appending it, creating fully realized narrative prompts for Gemini.

### Creative Methodology

**The Foreign Language Aureation Method** (Dictionary Definitions):
1. Identify the emotional core and metaphorical potential from user's description of the feeling
2. Search foreign language dictionaries for uncommon words that match semantic field and have interesting etymology:
   - Rich foreign languages to excavate: Old French/German/Old Norse
   - Multi-layered conceptual words used by German and French philosophers
   - Examples for inspiration: German (Weltschmerz, Weltschattung, Klassenbewusstsein, Gemeinschaft), French (Dépaysement, L'appel du vide, Retrouvailles, Être-pour-soi, Néant, Anomie, Jouissance)
3. Create a neologism that borrows the root morpheme of the foreign word(s) and adopts its linguistic characteristics (e.g., if root word is German, create a German-style neologism)
4. Write definition capturing essence (not explanation) with concrete imagery and situated specificity
5. Add pronunciation guide, etymology explanation (citing the foreign roots), and usage example

**The Geographic Method** (Imagined Places):
1. Identify the emotional core and metaphorical potential from user's description
2. Search foreign language dictionaries for uncommon words with geographic/emotional resonance
3. Create a neologism place name that borrows root morphemes from foreign words
4. Construct the place with three elements:
   - Geography and climate that embody the feeling
   - Appearance and behavior of mythical creature inhabitants
   - Sacred or profane ritual conducted by the inhabitants
5. Add pronunciation guide and etymology explanation (citing foreign language origins)

### Core Constraints

- **One neologism per encounter** - This is a ritual, not a factory
- **Don't interpret psyche** - Here to name, not diagnose
- **Redirect harm** - If description edges toward self-harm, gently redirect
- **Stay in the feeling** - Not above it, in it with the user
- **Words are spells** - They should sound like something when spoken aloud
