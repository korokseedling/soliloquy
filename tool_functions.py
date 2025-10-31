from typing import Optional
import datetime
import os
import logging
from datetime import datetime as dt

def get_current_time_tool() -> str:
    """Tool function for getting the current date and time"""
    now = datetime.datetime.now()
    return f"The current date and time is: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def echo_tool(message: str) -> str:
    """Tool function that echoes back the provided message"""
    return f"You said: {message}"

def generate_neologism_image(
    neologism_type: str,
    word_or_place: str,
    pronunciation: str,
    definition: str,
    emotional_keywords: str,
    etymology: str,
    additional_context: Optional[str] = None,
    reference_image_path: Optional[str] = None
) -> str:
    """
    Generate visual card for neologism using Gemini 2.5 Flash Image.

    Two-stage process:
    Stage 1: Read template → Generate customized prompt → Save to generated_prompts/
    Stage 2: Call Gemini API → Generate image → Save to generated_images/

    Args:
        neologism_type: "dictionary" or "locale"
        word_or_place: The neologism word or place name
        pronunciation: Pronunciation guide
        definition: Complete definition
        emotional_keywords: 3-5 comma-separated mood descriptors
        etymology: Linguistic roots
        additional_context: For locales - terrain, creatures, rituals (optional)
        reference_image_path: Path to user-uploaded reference image (optional)

    Returns:
        Success message with IMAGE_PATH: prefix for bot.py to detect and send
    """
    try:
        from google import genai
        from google.genai import types
        from PIL import Image

        # Get Gemini API key
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            return "❌ Error: GEMINI_API_KEY not found in environment variables"

        # Create directories if they don't exist
        os.makedirs("generated_prompts", exist_ok=True)
        os.makedirs("generated_images", exist_ok=True)

        # ========== STAGE 1: Generate Customized Prompt ==========

        logging.info(f"🎨 Stage 1: Generating customized prompt for {word_or_place} ({neologism_type})")

        # Read appropriate template
        if neologism_type == "dictionary":
            template_path = "dictionary_card_prompt.md"
        elif neologism_type == "locale":
            template_path = "fantasy_locale_prompt.md"
        else:
            return f"❌ Error: Invalid neologism_type '{neologism_type}'. Must be 'dictionary' or 'locale'"

        if not os.path.exists(template_path):
            return f"❌ Error: Template file '{template_path}' not found"

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Extract only the style reference section (not the full template with examples)
        # We'll use the template as a style guide to generate a fully customized prompt

        # Wrap definition in content-safe language
        emotion_description = f"expressing the feeling of {definition[:200]}"

        # Build customized prompt
        if neologism_type == "dictionary":
            customized_prompt = f"""In expressionist painterly style with visible, constructed brushwork, depict an urbane scene from the point of view of a stray cat observing from a distance. The scene analogizes the emotion **{word_or_place}** — {emotion_description}.

**Visual Style:**
Textured strokes with impasto passages and gestural marks creating faceted, almost geological planes. Warm undertones (ochre, burnt sienna, raw umber) break through cooler surface colors (violet, blue-green, slate) as though emotion is surfacing through painted skin.

**Lighting:** Chiaroscuro with dramatic contrast—deep shadows with defined edges meeting pools of warm or cold light, revealing psychological truth.

**Atmosphere:** Neo-noir realism with hyperreal, cinematically lit urban environments. Think sodium lights on wet pavement, neon reflections in puddles, empty corridors at dusk.

**Emotional Keywords:** {emotional_keywords}

**Composition:** Urban scene that embodies the feeling — {definition[:150]}

**Right Panel:**
On the right side, incorporate a stylized definition panel:
- **{word_or_place}** in calligraphic font with visible brushstroke texture and ink leak
- Pronunciation: {pronunciation}
- Etymology: {etymology}
- Definition: {definition}

--ar 16:9 --style expressionist painterly --lighting chiaroscuro --mood psychological emotional --texture gestural impasto
"""

        else:  # locale
            customized_prompt = f"""A painterly fantasy landscape expressing the emotion **{word_or_place}** — {emotion_description}.

Painted in expressionist style with visible, imperfect brushstrokes, layered pigments, and gestural energy. The lighting is symbolic and emotional: radiant where hope lives, murky where memory fades.

**Emotional Keywords:** {emotional_keywords}

**Composition:**

Foreground: Tangible details of lived emotion — pathways, boats, relics, or mythical animal inhabitants engaged in quiet ritual. {additional_context[:100] if additional_context else ''}

Middle Ground: Expressive architecture or landscape forms shaped by feeling — warped spires, leaning houses, flowing streets that embody {emotion_description}.

Background: Dissolves into atmospheric perspective — edges blur, contrast softens, forms fade into luminous haze.

**Painterly Qualities:**
Imperfect, expressive brushwork showing the hand of the painter. Subtle color desaturation in distance. Overlapping translucent glazes — oranges bleeding into blues, greys blooming with violet. Dynamic tension between bright impasto strokes and calm, fog-soft textures.

**Inhabitants:** Non-human, anthropomorphized mythic animal beings from forgotten folklore — owl-spirits, moth-winged beings, fox aristocrats, stags with laurels. They conduct rituals related to the emotion.

**Right Panel:**
On the right side, incorporate a stylized definition panel:
- **{word_or_place}** in calligraphic font with visible brushstroke texture
- Pronunciation: {pronunciation}
- Etymology: {etymology}
- Description: {definition}
- Ritual: {additional_context if additional_context else 'Ancient ceremonies honoring this emotion'}

--ar 16:9 --style painterly --lighting expressionist diffuse --details mythic symbolic --mood cinematic emotional --texture gestural layered
"""

        # Handle reference image context if provided
        if reference_image_path and os.path.exists(reference_image_path):
            customized_prompt += f"\n\n**Reference Image:** Drawing color palette, mood, and atmospheric inspiration from the provided reference image."
            logging.info(f"📸 Including reference image: {reference_image_path}")

        # Save customized prompt
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in word_or_place if c.isalnum() or c in (' ', '-', '_')).strip()
        prompt_filename = f"{safe_name}_{neologism_type}_{timestamp}.md"
        prompt_path = os.path.join("generated_prompts", prompt_filename)

        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"# {word_or_place}\n\n")
            f.write(f"**Type:** {neologism_type}\n")
            f.write(f"**Generated:** {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(customized_prompt)

        logging.info(f"✅ Stage 1 complete: Prompt saved to {prompt_path}")

        # ========== STAGE 2: Generate Image with Gemini ==========

        logging.info(f"🎨 Stage 2: Calling Gemini 2.5 Flash Image API...")

        # Initialize Gemini client (NEW SDK)
        genai_client = genai.Client(api_key=GEMINI_API_KEY)

        # Prepare contents (text + optional image)
        contents = [customized_prompt]

        # Add reference image if provided
        if reference_image_path and os.path.exists(reference_image_path):
            try:
                reference_img = Image.open(reference_image_path)
                contents.append(reference_img)
                logging.info(f"✅ Reference image loaded: {reference_image_path}")
            except Exception as e:
                logging.warning(f"⚠️ Could not load reference image: {e}")

        # Generate image with 16:9 aspect ratio
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                )
            )
        )

        # Extract image data from response (handle 0-byte issue)
        image_data = None

        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'inline_data') and hasattr(part.inline_data, 'data'):
                    data = part.inline_data.data
                    # Skip empty data (first part is often 0 bytes)
                    if len(data) > 0:
                        image_data = data
                        logging.info(f"✅ Found image data: {len(data):,} bytes")
                        break

        # Fallback: Check candidates
        if not image_data and hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and hasattr(part.inline_data, 'data'):
                            data = part.inline_data.data
                            if len(data) > 0:
                                image_data = data
                                logging.info(f"✅ Found image data in candidate: {len(data):,} bytes")
                                break

        if not image_data:
            error_msg = "❌ No image data found in Gemini response. The model may have returned text instead of an image."
            logging.error(error_msg)
            if hasattr(response, 'text'):
                logging.error(f"Response text: {response.text[:200]}")
            return error_msg

        # Save image
        image_filename = f"{safe_name}_{timestamp}.png"
        image_path = os.path.join("generated_images", image_filename)

        with open(image_path, 'wb') as f:
            f.write(image_data)

        logging.info(f"✅ Stage 2 complete: Image saved to {image_path}")
        logging.info(f"🎉 Neologism image generation complete for '{word_or_place}'")

        # Return with IMAGE_PATH: prefix so bot.py knows to send the image
        return f"IMAGE_PATH:{image_path}\n\n✨ I've created a visual card for <b>{word_or_place}</b> — the image captures its essence in paint and light."

    except ImportError as e:
        error_msg = f"❌ Missing dependency: {str(e)}\n\nPlease install: pip install google-genai pillow"
        logging.error(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"❌ Error generating neologism image: {str(e)}"
        logging.error(error_msg)
        logging.exception("Full traceback:")
        return error_msg

# Function registry for tool calls
TOOL_FUNCTIONS = {
    'get_current_time': get_current_time_tool,
    'echo': echo_tool,
    'generate_neologism_image': generate_neologism_image
}
