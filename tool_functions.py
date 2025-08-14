from typing import Optional
from lta_integration import LTADataManager, find_bus_stops_for_location

# Global variables (will be initialized in bot.py)
lta_manager = None

def get_bus_arrival_tool(bus_stop_code: str, service_no: Optional[str] = None) -> str:
    """Tool function for getting bus arrival information with enhanced error handling for Telegram"""
    result = lta_manager.get_bus_arrival(bus_stop_code, service_no)
    
    if 'error' in result:
        error_type = result.get('error_type', 'unknown')
        error_msg = result['error']
        
        # Provide specific guidance based on error type
        if error_type == 'auth':
            return f"🔐 **Authentication Error**\n{error_msg}\n\nAdmin needs to check the LTA API key!"
        elif error_type == 'not_found':
            return f"❌ **Bus Stop Not Found**\n{error_msg}\n\n💡 **Try:**\n• Check if the bus stop code is correct (5 digits)\n• Search by location name instead\n• Make sure it's an active bus stop"
        elif error_type == 'rate_limit':
            return f"🚦 **Too Many Requests**\n{error_msg}\n\nPlease wait a bit before trying again!"
        elif error_type == 'timeout':
            return f"⏰ **Request Timeout**\n{error_msg}\n\nThe API is slow. Please try again!"
        elif error_type == 'connection':
            return f"🌐 **Connection Error**\n{error_msg}\n\nCheck your internet connection and try again."
        else:
            return f"❌ **Error:** {error_msg}"
    
    if result.get('status') != 'success':
        return f"❌ Unexpected API response for bus stop {bus_stop_code}"
    
    services = result.get('services', [])
    if not services:
        return f"ℹ️ **No bus services found** for bus stop {bus_stop_code}\n\nThis stop may not be active or may not have scheduled services."
    
    response = f"🚌 **Bus arrivals for stop {bus_stop_code}**\n⏰ *Updated: {result['timestamp']}*\n\n"
    
    for service in services:
        if service_no and service['service_no'] != service_no:
            continue
            
        response += f"**🚌 Service {service['service_no']}** ({service['operator']}):\n"
        
        buses = [service['next_bus'], service['next_bus_2'], service['next_bus_3']]
        bus_labels = ['Next', '2nd', '3rd']
        
        for i, bus in enumerate(buses):
            if bus['available']:
                if bus['minutes_to_arrival'] is not None:
                    if bus['minutes_to_arrival'] <= 0:
                        arrival_text = "**Arriving now** 🏃‍♂️"
                    elif bus['minutes_to_arrival'] == 1:
                        arrival_text = "**1 minute**"
                    else:
                        arrival_text = f"**{bus['minutes_to_arrival']} minutes**"
                else:
                    arrival_text = "N/A"
                
                response += f"  • {bus_labels[i]}: {arrival_text} - {bus['load']}\n"
            else:
                response += f"  • {bus_labels[i]}: No data available\n"
        
        response += "\n"
    
    return response

def find_bus_stops_by_location_tool(location_query: str, max_results: int = 5) -> str:
    """Tool function for finding bus stops by location query with enhanced feedback for Telegram"""
    matches = find_bus_stops_for_location(location_query, max_results)
    
    if not matches:
        return f"❌ **No bus stops found** matching '{location_query}'\n\n💡 **Try:**\n• Different spelling or shorter search term\n• Landmark names like 'ION Orchard' or 'Ang Mo Kio Hub'\n• Area names like 'Marina Bay' or 'Jurong'\n• Check for typos"
    
    response = f"🔍 **Found {len(matches)} bus stops** near '{location_query}':\n\n"
    
    for i, match in enumerate(matches, 1):
        response += f"**{i}. {match['Description']}** (Code: {match['BusStopCode']})\n"
        response += f"📍 {match['RoadName']}\n"
        response += f"🎯 Match: {match['similarity_score']:.1%}\n\n"
    
    response += "💡 **Reply with the number** (e.g., '1') to get bus arrivals!"
    
    return response

def get_bus_arrivals_by_location_tool(location_query: str, service_no: Optional[str] = None, max_stops: int = 5) -> str:
    """Tool function for getting bus arrival information by location query - DEPRECATED, use 2-step approach"""
    # Find matching bus stops
    matches = find_bus_stops_for_location(location_query, max_stops)
    
    if not matches:
        return f"❌ **No bus stops found** matching '{location_query}'\n\nPlease try a different search term or be more specific."
    
    # Initialize results
    response = f"🔍 **Bus arrivals near '{location_query}'**\nFound {len(matches)} stops:\n\n"
    
    successful_stops = 0
    
    # Try to get arrival data for each matching stop
    for i, match in enumerate(matches, 1):
        bus_stop_code = match['BusStopCode']
        description = match['Description']
        road_name = match['RoadName']
        
        response += f"**{i}. {description}** ({bus_stop_code})\n📍 {road_name}\n"
        
        # Get bus arrival data
        arrival_data = lta_manager.get_bus_arrival(bus_stop_code, service_no)
        
        if 'error' in arrival_data:
            error_type = arrival_data.get('error_type', 'unknown')
            if error_type == 'not_found':
                response += "❌ Not found in API\n"
            elif error_type == 'timeout':
                response += "⏰ Timeout - try again\n"
            else:
                response += f"❌ Error: {arrival_data['error']}\n"
        
        elif arrival_data.get('status') == 'success':
            services = arrival_data.get('services', [])
            
            if not services:
                response += "ℹ️ No services available\n"
            else:
                successful_stops += 1
                response += "✅ **Live arrivals:**\n"
                
                for service in services[:3]:  # Limit to 3 services for readability
                    if service_no and service['service_no'] != service_no:
                        continue
                        
                    next_bus = service['next_bus']
                    if next_bus['available'] and next_bus['minutes_to_arrival'] is not None:
                        if next_bus['minutes_to_arrival'] <= 0:
                            arrival_text = "Arriving now"
                        else:
                            arrival_text = f"{next_bus['minutes_to_arrival']}min"
                        
                        response += f"  🚌 {service['service_no']}: **{arrival_text}** - {next_bus['load']}\n"
        
        response += "\n"
        
        # Stop after showing 3 stops to keep message manageable
        if i >= 3:
            break
    
    if successful_stops == 0:
        response += "❌ **No live data available** for these stops.\nTry again or use specific bus stop codes."
    
    return response

def get_carpark_availability_tool(carpark_id: Optional[str] = None, area: Optional[str] = None) -> str:
    """Tool function for getting carpark availability information for Telegram"""
    result = lta_manager.get_carpark_availability(carpark_id, area)
    
    if 'error' in result:
        error_type = result.get('error_type', 'unknown')
        error_msg = result['error']
        
        if error_type == 'request':
            return f"🌐 **API Request Failed**\n{error_msg}\n\nCheck internet and try again."
        elif error_type == 'json':
            return f"📄 **Data Format Error**\n{error_msg}\n\nAPI returned invalid data."
        else:
            return f"❌ **Error:** {error_msg}"
    
    if not result['carparks']:
        if carpark_id:
            return f"❌ **No carpark found** with ID `{carpark_id}`\n\n💡 Try searching by area instead."
        elif area:
            return f"❌ **No carparks found** in area `{area}`\n\n💡 Try a different area name."
        else:
            return "❌ **No carpark data available** at this time."
    
    response = f"🅿️ **Carpark availability**\n⏰ *Updated: {result['timestamp']}*\n\n"
    
    # Limit to 8 results for mobile readability
    for carpark in result['carparks'][:8]:
        response += f"**🏢 {carpark['development']}**\n"
        response += f"📍 {carpark['location']}\n"
        response += f"🚗 **{carpark['available_lots']} lots available** ({carpark['lot_type']})\n"
        response += f"🆔 {carpark['carpark_id']} | 📍 {carpark['area']}\n\n"
    
    if len(result['carparks']) > 8:
        response += f"... and **{len(result['carparks']) - 8} more** carparks available"
    
    return response

# Function registry for tool calls
TOOL_FUNCTIONS = {
    'get_bus_arrival': get_bus_arrival_tool,
    'find_bus_stops_by_location': find_bus_stops_by_location_tool,
    'get_bus_arrivals_by_location': get_bus_arrivals_by_location_tool,
    'get_carpark_availability': get_carpark_availability_tool
}