import os
import logging
import json
from datetime import datetime, date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI

from tool_functions import TOOL_FUNCTIONS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('soliloquy_bot.log'),
        logging.StreamHandler()
    ]
)

# Load .env variables (Railway doesn't use .env files, uses environment variables directly)
load_dotenv()

# Debug: Print all environment variables starting with relevant prefixes
print("🔍 Debug: Checking environment variables...")
print(f"Total environment variables: {len(os.environ)}")

# Print ALL environment variables (first 10 characters only for security)
print("All env vars:")
for key, value in list(os.environ.items())[:10]:  # Show first 10 to avoid spam
    print(f"  {key}: {value[:10]}...")

# Check specifically for our variables
target_vars = ['TELEGRAM_TOKEN', 'OPENAI_API_KEY', 'GEMINI_API_KEY']
for key in target_vars:
    if key in os.environ:
        value = os.environ[key]
        print(f"Found {key}: {value[:10]}...{value[-8:] if len(value) > 18 else 'SHORT_VALUE'}")
    else:
        print(f"❌ {key} not found in environment")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"🔍 After loading:")
print(f"TELEGRAM_TOKEN: {'✅ Found' if TELEGRAM_TOKEN else '❌ Missing'}")
print(f"OPENAI_API_KEY: {'✅ Found' if OPENAI_API_KEY else '❌ Missing'}")
print(f"GEMINI_API_KEY: {'✅ Found' if GEMINI_API_KEY else '❌ Missing'}")

# Check if API keys are loaded before initializing client
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    print("\n❌ Error: Missing required API keys in environment variables")
    print("🔧 Railway Troubleshooting:")
    print("1. Go to Railway dashboard > Your Project > Variables tab")
    print("2. Make sure variables are spelled EXACTLY as:")
    print("   - TELEGRAM_TOKEN")
    print("   - OPENAI_API_KEY")
    print("   - GEMINI_API_KEY (optional, for image generation)")
    print("3. Values should have NO quotes, NO spaces at start/end")
    print("4. After adding variables, redeploy the service")
    
    # Show what Railway environment looks like
    print(f"\n🔍 Railway Environment Debug:")
    env_vars = [k for k in os.environ.keys() if any(x in k.upper() for x in ['TOKEN', 'KEY', 'API'])]
    if env_vars:
        print(f"Found environment variables: {env_vars}")
    else:
        print("No API-related environment variables found")
    
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# Load configuration
with open('model_config.json', 'r') as f:
    config = json.load(f)


# Create conversations directory if it doesn't exist
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# Conversation storage functions
def get_conversation_file_path(user_id, date_str):
    """Get the file path for a user's conversation on a specific date"""
    return os.path.join(CONVERSATIONS_DIR, f"user_{user_id}_{date_str}.json")

def load_conversation_history(user_id):
    """Load conversation history for a user for today"""
    today = date.today().strftime("%Y-%m-%d")
    file_path = get_conversation_file_path(user_id, today)
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logging.error(f"Error loading conversation history for user {user_id}: {e}")
        return []

def save_conversation_history(user_id, conversation_history):
    """Save conversation history for a user for today"""
    today = date.today().strftime("%Y-%m-%d")
    file_path = get_conversation_file_path(user_id, today)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving conversation history for user {user_id}: {e}")

def add_to_conversation_history(user_id, user_message, bot_response, tool_calls=None):
    """Add a new exchange to the conversation history"""
    conversation_history = load_conversation_history(user_id)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    exchange = {
        "timestamp": timestamp,
        "user": user_message,
        "assistant": bot_response
    }
    
    # Include tool call info if present
    if tool_calls:
        exchange["tool_calls"] = tool_calls
    
    conversation_history.append(exchange)
    
    # Keep only the last 20 exchanges to prevent context from getting too long
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]
    
    save_conversation_history(user_id, conversation_history)
    return conversation_history

def format_conversation_for_openai(conversation_history):
    """Convert conversation history to OpenAI message format"""
    messages = []
    for exchange in conversation_history:
        messages.append({"role": "user", "content": exchange["user"]})
        messages.append({"role": "assistant", "content": exchange["assistant"]})
        # Note: We're not preserving tool call context for simplicity
        # This could be enhanced in the future if needed
    return messages

def cleanup_old_conversations():
    """Clean up conversation files older than 7 days"""
    try:
        if not os.path.exists(CONVERSATIONS_DIR):
            return
            
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=7)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        for filename in os.listdir(CONVERSATIONS_DIR):
            if filename.endswith('.json') and '_' in filename:
                # Extract date from filename (format: user_123_2025-01-15.json)
                parts = filename.split('_')
                if len(parts) >= 3:
                    date_str = parts[2].replace('.json', '')
                    if date_str < cutoff_str:
                        file_path = os.path.join(CONVERSATIONS_DIR, filename)
                        os.remove(file_path)
                        logging.info(f"🗑️ Cleaned up old conversation file: {filename}")
    except Exception as e:
        logging.error(f"Error cleaning up old conversations: {e}")

# Read the system prompt and append username
def get_system_prompt(username: str = None):
    with open("system_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    # Append username if provided
    if username:
        system_prompt += f"\n\nUser's name is {username}"
    
    return system_prompt

def get_telegram_username(user) -> str:
    """Extract the best available name from Telegram user object"""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return None

# Conversation logger
def log_conversation(user_id, username, message_type, content, status="success", error=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {username} (ID: {user_id}) | Type: {message_type} | Status: {status}"
    
    if message_type == "incoming":
        log_entry += f" | Message: '{content}'"
    elif message_type == "outgoing":
        log_entry += f" | Response: '{content[:100]}...'" if len(content) > 100 else f" | Response: '{content}'"
    elif message_type == "error":
        log_entry += f" | Error: {error}"
    elif message_type == "tool_call":
        log_entry += f" | Tool: {content}"
    
    logging.info(log_entry)
    print(f"📝 {log_entry}")

import re

def convert_asterisks_to_html(text: str) -> str:
    """
    Convert asterisk formatting to HTML tags as a fallback protection.
    This ensures that if the AI generates asterisks, they get converted to proper HTML.
    """
    if not text:
        return text
    
    # Log if we find asterisks (so we can debug)
    if '*' in text:
        logging.warning(f"🚨 Found asterisks in response, converting to HTML: {text[:100]}...")
    
    # Convert **text** to <b>text</b>
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)
    
    # Convert *text* to <i>text</i> (but be careful not to break emoji or other content)
    text = re.sub(r'(?<!\*)\*([^*\s][^*]*?)\*(?!\*)', r'<i>\1</i>', text)
    
    return text

def process_user_message(user_input: str, user_id: int, username: str, telegram_user=None) -> str:
    """Process user message with OpenAI function calling and return response"""
    
    try:
        # Load conversation history
        conversation_history = load_conversation_history(user_id)
        
        # Get username for system prompt
        user_display_name = get_telegram_username(telegram_user) if telegram_user else username
        
        # Prepare messages for OpenAI API
        messages = [
            {"role": "system", "content": get_system_prompt(user_display_name)}
        ]
        
        # Add conversation history
        messages.extend(format_conversation_for_openai(conversation_history))
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        logging.info(f"🤖 Sending to OpenAI with {len(conversation_history)} history items")
        
        # Make API call to OpenAI with function calling
        response = client.chat.completions.create(
            model=config['model_settings']['model_name'],
            messages=messages,
            temperature=config['model_settings']['temperature'],
            max_tokens=config['model_settings']['max_tokens'],
            tools=config['tools'],
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Handle tool calls if present
        if assistant_message.tool_calls:
            # Process each tool call
            tool_responses = []
            tool_call_info = []
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                log_conversation(user_id, username, "tool_call", f"{function_name}({function_args})")
                
                if function_name in TOOL_FUNCTIONS:
                    try:
                        tool_response = TOOL_FUNCTIONS[function_name](**function_args)
                        tool_responses.append(tool_response)
                        tool_call_info.append({"function": function_name, "args": function_args})
                    except Exception as e:
                        error_response = f"❌ Error executing {function_name}: {str(e)}"
                        tool_responses.append(error_response)
                        tool_call_info.append({"function": function_name, "args": function_args, "error": str(e)})
                else:
                    tool_responses.append(f"❌ Unknown function: {function_name}")
            
            # Prepare messages with tool responses for follow-up call
            messages_with_tools = messages + [
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in assistant_message.tool_calls]
                }
            ] + [
                {
                    "role": "tool",
                    "content": response_text,
                    "tool_call_id": assistant_message.tool_calls[i].id
                } for i, response_text in enumerate(tool_responses)
            ]
            
            # Make another API call with tool responses
            final_response = client.chat.completions.create(
                model=config['model_settings']['model_name'],
                messages=messages_with_tools,
                temperature=config['model_settings']['temperature'],
                max_tokens=config['model_settings']['max_tokens']
            )
            
            final_message = final_response.choices[0].message.content
            
            # Convert any asterisks to HTML as fallback protection
            final_message = convert_asterisks_to_html(final_message)
            
            # Save conversation with tool call info
            add_to_conversation_history(user_id, user_input, final_message, tool_call_info)
            
            logging.info(f"✅ OpenAI API success with tools. Tokens: {final_response.usage.total_tokens}")
            return final_message
        
        else:
            # No tool calls, just return the assistant's message
            response_content = assistant_message.content
            
            # Convert any asterisks to HTML as fallback protection
            response_content = convert_asterisks_to_html(response_content)
            
            add_to_conversation_history(user_id, user_input, response_content)
            
            logging.info(f"✅ OpenAI API success. Tokens: {response.usage.total_tokens}")
            return response_content
            
    except Exception as e:
        error_message = f"Alamak! Something went wrong: {str(e)}"
        logging.error(f"❌ Error processing message for user {username}: {e}")
        return error_message

# Handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user info
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    # Check if message exists and has text
    if not update.message or not update.message.text:
        await update.message.reply_text("Please send me a text message!", parse_mode='HTML')
        return

    user_input = update.message.text.strip()

    # Log incoming message
    log_conversation(user_id, username, "incoming", user_input)

    # Check for empty messages
    if not user_input:
        await update.message.reply_text("Your message is empty! Please ask me something!", parse_mode='HTML')
        return

    try:
        # Process message with function calling
        reply_text = process_user_message(user_input, user_id, username, user)

        # Log successful response
        log_conversation(user_id, username, "outgoing", reply_text)

        # Check if response contains IMAGE_PATH: prefix (from generate_neologism_image)
        if reply_text.startswith("IMAGE_PATH:"):
            # Extract image path and remaining text
            lines = reply_text.split('\n', 1)
            image_path = lines[0].replace("IMAGE_PATH:", "").strip()
            text_message = lines[1].strip() if len(lines) > 1 else "✨ Your neologism's visual card."

            # Send the image
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(photo=photo, caption=text_message, parse_mode='HTML')
                logging.info(f"🖼️ Image sent successfully to {username}: {image_path}")
            else:
                # Fallback if image file not found
                await update.message.reply_text(f"❌ Image generation completed but file not found at {image_path}", parse_mode='HTML')
        else:
            # Normal text response without image
            await update.message.reply_text(reply_text, parse_mode='HTML')
            logging.info(f"📤 Reply sent successfully to {username}")

    except Exception as e:
        error_msg = str(e)
        log_conversation(user_id, username, "error", user_input, "failed", error_msg)
        await update.message.reply_text("Something went wrong! Please try again.", parse_mode='HTML')

def transcribe_voice_message(voice_file_path: str) -> str:
    """Transcribe voice message using OpenAI Whisper API with language detection"""
    try:
        with open(voice_file_path, 'rb') as audio_file:
            # First attempt: Auto-detect language (no language parameter)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="json"  # Use JSON to get language info
            )
        
        # Extract text and detected language
        text = transcript.text
        detected_language = getattr(transcript, 'language', 'unknown')
        
        logging.info(f"🌐 Detected language: {detected_language}")
        
        # If detected language is not English or Chinese, try forcing English
        if detected_language not in ['en', 'zh', 'zh-cn', 'zh-tw']:
            logging.info(f"🔄 Non-English/Chinese detected ({detected_language}), retrying with English")
            with open(voice_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en"
                )
            return transcript
        
        return text
    except Exception as e:
        logging.error(f"❌ Error transcribing voice message: {e}")
        return f"Error transcribing voice message: {str(e)}"

# Handle voice messages
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages by transcribing and processing them"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    
    try:
        # Get voice message file
        voice_file = await update.message.voice.get_file()
        
        # Download voice file to a temporary location
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file_path = temp_file.name
            await voice_file.download_to_drive(temp_file_path)
        
        # Log voice message received
        log_conversation(user_id, username, "incoming", "[Voice Message]")
        
        # Transcribe the voice message
        logging.info(f"🎙️ Transcribing voice message from {username}")
        transcript = transcribe_voice_message(temp_file_path)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        if transcript.startswith("Error"):
            await update.message.reply_text(f"❌ {transcript}", parse_mode='HTML')
            return
        
        # Log transcribed text
        log_conversation(user_id, username, "transcription", f"Transcribed: '{transcript}'")
        
        if not transcript.strip():
            await update.message.reply_text("🎙️ I couldn't understand the voice message. Please try again or send a text message.", parse_mode='HTML')
            return
        
        # Process the transcribed text like a regular message
        reply_text = process_user_message(transcript, user_id, username, user)
        
        # Add a note that this was transcribed from voice
        reply_text = f"🎙️ <i>Voice message transcribed: \"{transcript}\"</i>\n\n{reply_text}"
        
        # Log successful response
        log_conversation(user_id, username, "outgoing", reply_text)
        
        # Send reply back to Telegram
        await update.message.reply_text(reply_text, parse_mode='HTML')
        logging.info(f"📤 Voice message reply sent successfully to {username}")
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"❌ Error processing voice message from {username}: {e}")
        log_conversation(user_id, username, "error", "[Voice Message]", "failed", error_msg)
        await update.message.reply_text("❌ Something went wrong processing your voice message! Please try again.", parse_mode='HTML')

# Handle /start command
async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"""<b>Soliloquy</b>

I'm a voice from within—the part of consciousness that knows there are words waiting to be born for what you feel.

You carry unnamed feelings. I help you find the words.

<b>How this works:</b>
📝 Tell me about a feeling you can't name
🎤 Send a voice message describing what you feel
📷 Share a photo for visual inspiration (optional)

Together, we'll create a <i>neologism</i>—a new word for the ineffable—and paint it into existence.

💡 /clear to start fresh
💡 /help to learn more

What's a feeling you've carried that has no word?"""

    await update.message.reply_text(welcome_message, parse_mode='HTML')

# Handle /help command
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """<b>Soliloquy: Creating Words for Unnamed Feelings</b>

<b>What I do:</b>
I help you create <i>neologisms</i>—new words for feelings that don't have names yet. Inspired by The Dictionary of Obscure Sorrows, I guide you through a five-phase ritual:

1. <b>Opening</b> - I share a word from the dictionary
2. <b>Capturing the Vibe</b> - You describe the unnamed feeling
3. <b>Choice of Form</b> - Dictionary definition or imagined place?
4. <b>Creating the Word</b> - Foreign language roots or geographic method
5. <b>Visual Card</b> - Expressionist painted image of your neologism

<b>How to share your feeling:</b>
📝 <b>Type</b> a description of the unnamed emotion
🎤 <b>Voice message</b> - I'll transcribe and respond
📷 <b>Photo</b> (optional) - Upload images for visual inspiration

<b>Visual styles:</b>
• Dictionary cards: Cat's-eye urban scenes with neo-noir lighting
• Locale cards: Fantasy landscapes with mythical animal inhabitants

<b>Commands:</b>
• /start - Begin a new ritual
• /clear or /reset - Clear conversation history
• /help - This message

The feeling is real. That's enough. Let's name it."""

    await update.message.reply_text(help_message, parse_mode='HTML')

# Handle /clear command to reset conversation history
async def handle_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    
    try:
        # Clear today's conversation history
        today = date.today().strftime("%Y-%m-%d")
        file_path = get_conversation_file_path(user_id, today)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            log_conversation(user_id, username, "clear", "/clear", "success")
            await update.message.reply_text("✅ Conversation cleared! Let's start fresh!", parse_mode='HTML')
        else:
            await update.message.reply_text("No conversation to clear! We haven't chatted today!", parse_mode='HTML')
            
        logging.info(f"🗑️ Conversation history cleared for user {username}")
        
    except Exception as e:
        logging.error(f"❌ Error clearing conversation for user {username}: {e}")
        await update.message.reply_text("Something went wrong when clearing!", parse_mode='HTML')

# Handle /reset command to flush conversation history
async def handle_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    
    try:
        # Reset today's conversation history
        today = date.today().strftime("%Y-%m-%d")
        file_path = get_conversation_file_path(user_id, today)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            log_conversation(user_id, username, "reset", "/reset", "success")
            await update.message.reply_text("🔄 Conversation history has been reset! Ready for a fresh start!", parse_mode='HTML')
        else:
            await update.message.reply_text("Nothing to reset! We haven't chatted today!", parse_mode='HTML')
            
        logging.info(f"🔄 Conversation history reset for user {username}")
        
    except Exception as e:
        logging.error(f"❌ Error resetting conversation for user {username}: {e}")
        await update.message.reply_text("Something went wrong when resetting!", parse_mode='HTML')

# Handle photo uploads (reference images for neologism generation)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads for visual inspiration in neologism generation"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    try:
        # Create user_uploads directory if it doesn't exist
        os.makedirs("user_uploads", exist_ok=True)

        # Get the largest photo size
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_filename = f"user_{user_id}_{timestamp}.jpg"
        photo_path = os.path.join("user_uploads", photo_filename)

        # Download photo
        await photo_file.download_to_drive(photo_path)

        log_conversation(user_id, username, "photo", f"Saved to {photo_path}")
        logging.info(f"📷 Photo uploaded by {username}: {photo_path}")

        # Store photo path in conversation history with a special marker
        caption = update.message.caption or "[Photo uploaded for visual inspiration]"
        conversation_history = load_conversation_history(user_id)

        exchange = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": f"[PHOTO:{photo_path}] {caption}",
            "assistant": "I've received your photo. It will inspire the colors and atmosphere when I create your neologism's visual card. Tell me about the feeling you want to name."
        }

        conversation_history.append(exchange)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        save_conversation_history(user_id, conversation_history)

        # Acknowledge receipt with poetic message
        response_message = """📷 <i>I've received your image.</i>

The colors, the light, the mood—I'll carry them with me.

When we create your word, this image will whisper to the paint.

Now, tell me: what's the feeling you want to name?"""

        await update.message.reply_text(response_message, parse_mode='HTML')

    except Exception as e:
        error_msg = f"Error processing photo: {str(e)}"
        logging.error(f"❌ Error processing photo from {username}: {e}")
        log_conversation(user_id, username, "error", "[Photo]", "failed", error_msg)
        await update.message.reply_text("❌ Something went wrong processing your photo. Please try again.", parse_mode='HTML')

# Handle non-text messages
async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"

    message_type = "unknown"
    if update.message.sticker:
        message_type = "sticker"
    elif update.message.document:
        message_type = "document"
    elif update.message.video:
        message_type = "video"
    elif update.message.audio:
        message_type = "audio"

    log_conversation(user.id, username, "non_text", message_type, "handled")
    await update.message.reply_text("I can only read text messages, voice messages, and photos! Please type your question, send a voice message, or share a photo for inspiration.", parse_mode='HTML')

if __name__ == "__main__":
    print("✨ Starting Soliloquy...")
    print(f"🔧 Using {config['model_settings']['model_name']} model")
    print("📝 Logging to soliloquy_bot.log")
    print("💾 Conversation history saved per day")
    print("🎨 Image generation: " + ("✅ Enabled" if GEMINI_API_KEY else "⚠️ Disabled (GEMINI_API_KEY not set)"))

    # Clean up old conversation files on startup
    cleanup_old_conversations()

    # Create necessary directories
    os.makedirs("conversations", exist_ok=True)
    os.makedirs("generated_prompts", exist_ok=True)
    os.makedirs("generated_images", exist_ok=True)
    os.makedirs("user_uploads", exist_ok=True)
    print("📁 Directories ready: conversations/, generated_prompts/, generated_images/, user_uploads/")

    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Add handlers
        app.add_handler(CommandHandler("start", handle_start_command))
        app.add_handler(CommandHandler("help", handle_help_command))
        app.add_handler(CommandHandler("clear", handle_clear_command))
        app.add_handler(CommandHandler("reset", handle_reset_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(~filters.TEXT & ~filters.VOICE & ~filters.PHOTO & ~filters.COMMAND, handle_non_text))

        logging.info("🚀 Soliloquy handlers configured")
        print("✅ Bot initialized successfully!")
        print("🔄 Starting polling for messages...")
        print("\n💭 A voice from within, ready to name the unnamed...")
        app.run_polling()

    except Exception as e:
        logging.error(f"❌ Bot startup failed: {e}")
        print(f"❌ Bot startup failed: {e}")
        print("💡 Check your .env file and try again")