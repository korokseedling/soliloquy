import os
import logging
import json
from datetime import datetime, date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI

from lta_integration import LTADataManager, BusStopMatcher
from tool_functions import TOOL_FUNCTIONS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lepak_driver_bot.log'),
        logging.StreamHandler()
    ]
)

# Load .env variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LTA_API_KEY = os.getenv("LTA_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Load configuration
with open('model_config.json', 'r') as f:
    config = json.load(f)

# Initialize LTA components
lta_manager = LTADataManager(LTA_API_KEY, config['lta_api_settings']['base_url'], config)
bus_stop_matcher = BusStopMatcher()

# Set global lta_manager for tool functions
import tool_functions
tool_functions.lta_manager = lta_manager

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

# Read the system prompt
def get_system_prompt():
    with open("system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()

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

def process_user_message(user_input: str, user_id: int, username: str) -> str:
    """Process user message with OpenAI function calling and return response"""
    
    try:
        # Load conversation history
        conversation_history = load_conversation_history(user_id)
        
        # Prepare messages for OpenAI API
        messages = [
            {"role": "system", "content": get_system_prompt()}
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
            
            # Save conversation with tool call info
            add_to_conversation_history(user_id, user_input, final_message, tool_call_info)
            
            logging.info(f"✅ OpenAI API success with tools. Tokens: {final_response.usage.total_tokens}")
            return final_message
        
        else:
            # No tool calls, just return the assistant's message
            response_content = assistant_message.content
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
        await update.message.reply_text("Eh, I need a text message leh! Can type your question about buses or parking?")
        return
    
    user_input = update.message.text.strip()
    
    # Log incoming message
    log_conversation(user_id, username, "incoming", user_input)
    
    # Check for empty messages
    if not user_input:
        await update.message.reply_text("Your message is empty lah! Ask me about bus arrivals or parking! 🚌🅿️")
        return
    
    try:
        # Process message with function calling
        reply_text = process_user_message(user_input, user_id, username)
        
        # Log successful response
        log_conversation(user_id, username, "outgoing", reply_text)
        
        # Send reply back to Telegram
        await update.message.reply_text(reply_text)
        logging.info(f"📤 Reply sent successfully to {username}")
        
    except Exception as e:
        error_msg = str(e)
        log_conversation(user_id, username, "error", user_input, "failed", error_msg)
        await update.message.reply_text("Alamak! Something went wrong lah! Can try again? 😰")

# Handle /start command
async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"""🚌 **Welcome to Lepak Driver!** 

Hi {user.first_name}! I'm your Singapore transit assistant. I can help you with:

🚌 **Real-time bus arrivals**
• "When is bus 174 at Ang Mo Kio Hub?"
• "Bus arrivals at ION Orchard"
• "Check bus stop 28009"

🅿️ **Carpark availability**
• "Parking at Marina Bay"
• "How many lots at Jurong Point?"

Just ask me in natural language and I'll help you lepak around Singapore! 😊

💡 Use /clear to reset our conversation
💡 Use /help for more examples"""
    
    await update.message.reply_text(welcome_message)

# Handle /help command
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """🚌 **Lepak Driver Help**

**Bus Arrival Queries:**
• "Bus 174 at Ang Mo Kio Hub"
• "When is the next bus at ION Orchard?"
• "Bus arrivals at stop 28009"
• "Is bus 36 crowded now?"

**Parking Queries:**
• "Parking availability at Marina Bay"
• "How many lots at Jurong Point?"
• "Carparks in Orchard area"

**Commands:**
• /start - Welcome message
• /clear - Reset conversation
• /help - This help message

Just type naturally and I'll understand! 🇸🇬"""
    
    await update.message.reply_text(help_message)

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
            await update.message.reply_text("✅ Conversation cleared! Let's start fresh! 🚌🅿️")
        else:
            await update.message.reply_text("No conversation to clear! We haven't chatted today! 🤔")
            
        logging.info(f"🗑️ Conversation history cleared for user {username}")
        
    except Exception as e:
        logging.error(f"❌ Error clearing conversation for user {username}: {e}")
        await update.message.reply_text("Alamak! Something went wrong when clearing! 😰")

# Handle non-text messages
async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    
    message_type = "unknown"
    if update.message.sticker:
        message_type = "sticker"
    elif update.message.photo:
        message_type = "photo"
    elif update.message.voice:
        message_type = "voice"
    elif update.message.document:
        message_type = "document"
    
    log_conversation(user.id, username, "non_text", message_type, "handled")
    await update.message.reply_text("Wah! I can only read text messages leh! Can type your bus or parking question instead? 🚌🅿️")

if __name__ == "__main__":
    # Check if tokens are loaded
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not LTA_API_KEY:
        print("❌ Error: Please set TELEGRAM_TOKEN, OPENAI_API_KEY, and LTA_API_KEY in .env file")
        exit(1)
    
    print("🚌 Starting Lepak Driver bot...")
    print(f"📊 Loaded {len(bus_stop_matcher.bus_stops)} bus stops")
    print(f"🔧 Using {config['model_settings']['model_name']} model")
    print("📝 Logging to lepak_driver_bot.log")
    print("💾 Conversation history saved per day")
    
    # Clean up old conversation files on startup
    cleanup_old_conversations()
    
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", handle_start_command))
        app.add_handler(CommandHandler("help", handle_help_command))
        app.add_handler(CommandHandler("clear", handle_clear_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text))
        
        logging.info("🚀 Lepak Driver bot handlers configured")
        print("✅ Bot initialized successfully!")
        print("🔄 Starting polling for messages...")
        app.run_polling()
        
    except Exception as e:
        logging.error(f"❌ Bot startup failed: {e}")
        print(f"❌ Bot startup failed: {e}")
        print("💡 Check your .env file and try again")