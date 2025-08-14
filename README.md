# Lepak Driver - Telegram Bot

A Telegram bot that provides real-time Singapore transit information including bus arrivals and carpark availability.

## Features

### 🚌 Bus Information
- Real-time bus arrival times
- Bus crowding levels (Seats Available, Standing Available, Limited Standing)
- Location-based bus stop search
- Support for specific service numbers

### 🅿️ Parking Information  
- Real-time carpark availability
- HDB and major development carparks
- Filter by area or specific carpark ID

### 💬 Natural Language Support
- Understands colloquial Singaporean English
- Two-step workflow for location queries
- Conversation history maintained per day

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- OpenAI API Key
- LTA DataMall API Key

### 2. Installation

```bash
# Clone or copy the files to your directory
cd telegram_lepak_driver

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Configuration

Create a `.env` file with:
```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
LTA_API_KEY=your_lta_datamall_key
```

### 4. Run the Bot

```bash
python bot.py
```

## Usage Examples

### Bus Queries
- "When is bus 174 at Ang Mo Kio Hub?"
- "Bus arrivals at ION Orchard"
- "Check bus stop 28009"
- "Is bus 36 crowded now?"

### Parking Queries
- "Parking at Marina Bay"
- "How many lots at Jurong Point?"
- "Carparks in Orchard area"

### Commands
- `/start` - Welcome message and introduction
- `/help` - Show usage examples
- `/clear` - Reset conversation history

## Technical Details

- **Model**: OpenAI GPT-4o-mini with function calling
- **APIs**: LTA DataMall for real-time transit data
- **Rate Limiting**: Built-in API rate limiting
- **Conversation**: Daily conversation history with 20-message limit
- **Error Handling**: Comprehensive error handling with user-friendly messages

## File Structure

```
telegram_lepak_driver/
├── bot.py                    # Main bot application
├── lta_integration.py        # LTA API integration and bus stop matching
├── tool_functions.py         # OpenAI tool functions
├── model_config.json         # Model and API configuration
├── system_prompt.md          # System prompt for the bot
├── bus_stops_singapore.json  # Bus stop database for location matching
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── conversations/           # User conversation history (created on run)
```

## Deployment Options

### Local Development
Run directly with `python bot.py`

### Production (Heroku/Railway)
1. Add a `Procfile`:
   ```
   worker: python bot.py
   ```

2. Set environment variables in your platform's dashboard

3. Deploy and scale to 1 worker

## API Limits

- **LTA DataMall**: 500 requests/minute, 5000 requests/day
- **OpenAI**: Based on your API plan
- **Telegram**: No limits for typical usage

## Troubleshooting

1. **Bot not responding**: Check your `.env` file has all required tokens
2. **Bus data not loading**: Verify your LTA API key is valid
3. **Tool calls failing**: Ensure `bus_stops_singapore.json` is present
4. **Rate limiting**: Wait and try again, the bot has built-in rate limiting

## Support

Check the logs in `lepak_driver_bot.log` for detailed error information.