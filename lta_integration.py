import os
import json
import requests
import time
import difflib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

class LTADataManager:
    def __init__(self, api_key: str, base_url: str, config: Dict):
        self.api_key = api_key
        self.base_url = base_url
        self.config = config['lta_api_settings']
        self.headers = {
            'AccountKey': api_key,
            'Accept': 'application/json'
        }
        self.last_request_time = 0
        self.request_count = 0
    
    def _rate_limit(self):
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        min_interval = 60 / self.config['rate_limits']['requests_per_minute']
        
        if time_diff < min_interval:
            sleep_time = min_interval - time_diff
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_bus_arrival(self, bus_stop_code: str, service_no: Optional[str] = None) -> Dict:
        self._rate_limit()
        
        url = f"{self.base_url}{self.config['endpoints']['bus_arrival']}"
        params = {'BusStopCode': bus_stop_code}
        if service_no:
            params['ServiceNo'] = service_no
        
        try:
            print(f"🔍 Fetching bus arrivals for stop {bus_stop_code}...")
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=self.config['timeout']
            )
            
            print(f"📡 API Response: {response.status_code}")
            
            if response.status_code == 401:
                return {'error': 'API authentication failed. Please check your API key.', 'error_type': 'auth'}
            elif response.status_code == 429:
                return {'error': 'API rate limit exceeded. Please wait before retrying.', 'error_type': 'rate_limit'}
            elif response.status_code == 404:
                return {'error': f'Bus stop {bus_stop_code} not found in API.', 'error_type': 'not_found'}
            elif response.status_code != 200:
                return {'error': f'API request failed with status {response.status_code}', 'error_type': 'api_error'}
            
            response.raise_for_status()
            data = response.json()
            
            if 'Services' not in data:
                return {'error': f'Invalid API response format for stop {bus_stop_code}', 'error_type': 'invalid_format'}
            
            # Process and format the data
            services = data.get('Services', [])
            formatted_data = {
                'bus_stop_code': bus_stop_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'services': [],
                'status': 'success'
            }
            
            for service in services:
                service_data = {
                    'service_no': service.get('ServiceNo'),
                    'operator': service.get('Operator'),
                    'next_bus': self._format_bus_info(service.get('NextBus', {})),
                    'next_bus_2': self._format_bus_info(service.get('NextBus2', {})),
                    'next_bus_3': self._format_bus_info(service.get('NextBus3', {}))
                }
                formatted_data['services'].append(service_data)
            
            print(f"✅ Successfully fetched {len(services)} services for stop {bus_stop_code}")
            return formatted_data
            
        except requests.exceptions.Timeout:
            return {'error': f'Request timeout for bus stop {bus_stop_code}. Please try again.', 'error_type': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': f'Connection error for bus stop {bus_stop_code}. Please check your internet connection.', 'error_type': 'connection'}
        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed for stop {bus_stop_code}: {str(e)}', 'error_type': 'request'}
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON response for stop {bus_stop_code}: {str(e)}', 'error_type': 'json'}
        except Exception as e:
            return {'error': f'Unexpected error for stop {bus_stop_code}: {str(e)}', 'error_type': 'unknown'}
    
    def _format_bus_info(self, bus_info: Dict) -> Dict:
        if not bus_info:
            return {'available': False}
        
        # Convert arrival time to minutes
        estimated_arrival = bus_info.get('EstimatedArrival', '')
        if estimated_arrival:
            try:
                arrival_time = datetime.fromisoformat(estimated_arrival.replace('Z', '+00:00'))
                current_time = datetime.now(arrival_time.tzinfo)
                minutes_to_arrival = int((arrival_time - current_time).total_seconds() / 60)
            except:
                minutes_to_arrival = None
        else:
            minutes_to_arrival = None
        
        # Map load values to readable format
        load_mapping = {
            'SEA': 'Seats Available',
            'SDA': 'Standing Available', 
            'LSD': 'Limited Standing'
        }
        
        return {
            'available': True,
            'minutes_to_arrival': minutes_to_arrival,
            'load': load_mapping.get(bus_info.get('Load', ''), 'Unknown'),
            'feature': bus_info.get('Feature', ''),
            'type': bus_info.get('Type', '')
        }
    
    def get_carpark_availability(self, carpark_id: Optional[str] = None, area: Optional[str] = None) -> Dict:
        self._rate_limit()
        
        url = f"{self.base_url}{self.config['endpoints']['carpark_availability']}"
        params = {}
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=self.config['timeout']
            )
            response.raise_for_status()
            data = response.json()
            
            carparks = data.get('value', [])
            formatted_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'carparks': []
            }
            
            for carpark in carparks:
                # Filter by carpark_id if specified
                if carpark_id and carpark.get('CarParkID') != carpark_id:
                    continue
                    
                # Filter by area if specified (basic string matching)
                if area and area.lower() not in carpark.get('Development', '').lower():
                    continue
                
                carpark_data = {
                    'carpark_id': carpark.get('CarParkID'),
                    'area': carpark.get('Area'),
                    'development': carpark.get('Development'),
                    'location': carpark.get('Location'),
                    'available_lots': carpark.get('AvailableLots'),
                    'lot_type': carpark.get('LotType'),
                    'agency': carpark.get('Agency')
                }
                formatted_data['carparks'].append(carpark_data)
            
            return formatted_data
            
        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed: {str(e)}', 'error_type': 'request'}
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON response: {str(e)}', 'error_type': 'json'}


class BusStopMatcher:
    def __init__(self, bus_stops_file: str = 'bus_stops_singapore.json'):
        """Initialize the bus stop matcher with bus stops data"""
        try:
            with open(bus_stops_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bus_stops = data['bus_stops']
            print(f"✅ Loaded {len(self.bus_stops)} bus stops for matching")
        except FileNotFoundError:
            print(f"❌ Bus stops file {bus_stops_file} not found")
            self.bus_stops = []
        except Exception as e:
            print(f"❌ Error loading bus stops: {e}")
            self.bus_stops = []
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        if not text:
            return ""
        # Convert to lowercase, remove extra spaces, and normalize punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _calculate_similarity_score(self, query: str, bus_stop: Dict) -> Tuple[float, str]:
        """Calculate similarity score between query and bus stop"""
        query_norm = self._normalize_text(query)
        
        # Extract searchable text from bus stop
        road_name = self._normalize_text(bus_stop.get('RoadName', ''))
        description = self._normalize_text(bus_stop.get('Description', ''))
        bus_stop_code = bus_stop.get('BusStopCode', '')
        
        # Combine all searchable text
        combined_text = f"{road_name} {description}".strip()
        
        # Check for exact bus stop code match (highest priority)
        if query_norm == bus_stop_code.lower():
            return 1.0, f"Exact code match: {bus_stop_code}"
        
        # Check if query is contained in any field (high priority)
        if query_norm in combined_text:
            return 0.9, f"Contains '{query}' in {road_name} - {description}"
        
        # Check individual field matches
        road_similarity = difflib.SequenceMatcher(None, query_norm, road_name).ratio()
        desc_similarity = difflib.SequenceMatcher(None, query_norm, description).ratio()
        
        # Take the higher similarity score
        max_similarity = max(road_similarity, desc_similarity)
        match_field = "road name" if road_similarity > desc_similarity else "description"
        
        # Check for partial word matches
        query_words = query_norm.split()
        combined_words = combined_text.split()
        
        word_matches = 0
        for q_word in query_words:
            if len(q_word) > 2:  # Only consider words longer than 2 characters
                for c_word in combined_words:
                    if q_word in c_word or difflib.SequenceMatcher(None, q_word, c_word).ratio() > 0.8:
                        word_matches += 1
                        break
        
        # Boost score based on word matches
        if query_words:
            word_match_ratio = word_matches / len(query_words)
            max_similarity = max(max_similarity, word_match_ratio * 0.8)
        
        match_reason = f"Best match in {match_field} (score: {max_similarity:.2f})"
        
        return max_similarity, match_reason
    
    def find_matching_bus_stops(self, location_query: str, top_k: int = 5) -> List[Dict]:
        """Find top K matching bus stops for a location query"""
        if not self.bus_stops:
            return []
        
        if not location_query or not location_query.strip():
            return []
        
        # Calculate similarity scores for all bus stops
        matches = []
        
        for bus_stop in self.bus_stops:
            score, reason = self._calculate_similarity_score(location_query, bus_stop)
            
            if score > 0.1:  # Only consider matches with minimum similarity
                matches.append({
                    'bus_stop': bus_stop,
                    'similarity_score': score,
                    'match_reason': reason
                })
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top K matches
        return matches[:top_k]


def find_bus_stops_for_location(location_query: str, top_k: int = 5) -> List[Dict]:
    """Convenience function to find bus stops for a location"""
    matcher = BusStopMatcher()
    matches = matcher.find_matching_bus_stops(location_query, top_k)
    
    # Return just the bus stop data with codes for easy access
    return [{
        'BusStopCode': match['bus_stop']['BusStopCode'],
        'RoadName': match['bus_stop']['RoadName'], 
        'Description': match['bus_stop']['Description'],
        'similarity_score': match['similarity_score'],
        'match_reason': match['match_reason']
    } for match in matches]