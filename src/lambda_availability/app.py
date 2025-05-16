import os
import json
import logging
import sys
import requests
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils.bedrock_client import BedrockClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
bedrock_client = BedrockClient()

# Environment variables for external systems
LOYALTY_SYSTEM_URL = os.environ.get('LOYALTY_SYSTEM_URL', '')
AVAILABILITY_SYSTEM_URL = os.environ.get('AVAILABILITY_SYSTEM_URL', '')
API_KEY = os.environ.get('EXTERNAL_API_KEY', '')

def lambda_handler(event, context):
    """
    Lambda function handler for checking availability across travel systems.
    
    This function processes availability requests, checks inventory systems,
    and returns availability information for flights, hotels, or activities.
    
    Args:
        event: API Gateway event or direct Lambda invocation
        context: Lambda context
        
    Returns:
        Availability results
    """
    try:
        logger.info("Processing availability request")
        
        # Parse the request
        if event.get('body'):
            # API Gateway invocation
            body = json.loads(event.get('body', '{}'))
            request_type = body.get('type', '')
            search_params = body.get('params', {})
            user_id = body.get('user_id', '')
        else:
            # Direct Lambda invocation
            request_type = event.get('type', '')
            search_params = event.get('params', {})
            user_id = event.get('user_id', '')
        
        if not request_type:
            return create_response(400, {
                'error': 'Missing required parameter: type'
            })
        
        if not search_params:
            return create_response(400, {
                'error': 'Missing required parameter: params'
            })
        
        # Process based on request type
        availability_results = {}
        if request_type.lower() == 'flight':
            availability_results = check_flight_availability(search_params)
        elif request_type.lower() == 'hotel':
            availability_results = check_hotel_availability(search_params)
        elif request_type.lower() == 'activity':
            availability_results = check_activity_availability(search_params)
        elif request_type.lower() == 'package':
            availability_results = check_package_availability(search_params)
        else:
            return create_response(400, {
                'error': f'Unsupported request type: {request_type}'
            })
        
        # If user ID provided, check loyalty program status
        loyalty_info = {}
        if user_id and LOYALTY_SYSTEM_URL:
            loyalty_info = check_loyalty_status(user_id)
        
        # Combine results
        result = {
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'request_type': request_type,
            'search_params': search_params,
            'results': availability_results,
            'loyalty': loyalty_info
        }
        
        logger.info(f"Successfully processed {request_type} availability request")
        
        # Return based on invocation type
        if event.get('body'):
            return create_response(200, result)
        else:
            return result
        
    except Exception as e:
        logger.error(f"Error processing availability request: {str(e)}")
        error_response = {
            'error': f'Internal server error: {str(e)}'
        }
        
        if event.get('body'):
            return create_response(500, error_response)
        else:
            return error_response


def check_flight_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check flight availability based on search parameters.
    
    Args:
        params: Flight search parameters
        
    Returns:
        Dictionary with flight availability results
    """
    try:
        logger.info(f"Checking flight availability: {params}")
        
        # Required parameters
        origin = params.get('origin', '')
        destination = params.get('destination', '')
        departure_date = params.get('departure_date', '')
        
        if not all([origin, destination, departure_date]):
            return {
                'error': 'Missing required flight parameters',
                'available': False
            }
        
        # Optional parameters
        return_date = params.get('return_date', '')
        passengers = params.get('passengers', 1)
        cabin_class = params.get('cabin_class', 'economy')
        
        # In a real implementation, we would call an external flight booking API
        # For demonstration, we'll simulate the API call
        
        if AVAILABILITY_SYSTEM_URL:
            # Call external availability system
            response = call_availability_system('flight', params)
            return response
        else:
            # Simulate availability results
            return simulate_flight_availability(origin, destination, departure_date, return_date, passengers, cabin_class)
        
    except Exception as e:
        logger.error(f"Error checking flight availability: {str(e)}")
        return {
            'error': f'Error checking flight availability: {str(e)}',
            'available': False
        }


def check_hotel_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check hotel availability based on search parameters.
    
    Args:
        params: Hotel search parameters
        
    Returns:
        Dictionary with hotel availability results
    """
    try:
        logger.info(f"Checking hotel availability: {params}")
        
        # Required parameters
        location = params.get('location', '')
        check_in = params.get('check_in', '')
        check_out = params.get('check_out', '')
        
        if not all([location, check_in, check_out]):
            return {
                'error': 'Missing required hotel parameters',
                'available': False
            }
        
        # Optional parameters
        rooms = params.get('rooms', 1)
        guests = params.get('guests', 1)
        hotel_class = params.get('hotel_class', '')
        
        # In a real implementation, we would call an external hotel booking API
        # For demonstration, we'll simulate the API call
        
        if AVAILABILITY_SYSTEM_URL:
            # Call external availability system
            response = call_availability_system('hotel', params)
            return response
        else:
            # Simulate availability results
            return simulate_hotel_availability(location, check_in, check_out, rooms, guests, hotel_class)
        
    except Exception as e:
        logger.error(f"Error checking hotel availability: {str(e)}")
        return {
            'error': f'Error checking hotel availability: {str(e)}',
            'available': False
        }


def check_activity_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check activity availability based on search parameters.
    
    Args:
        params: Activity search parameters
        
    Returns:
        Dictionary with activity availability results
    """
    try:
        logger.info(f"Checking activity availability: {params}")
        
        # Required parameters
        location = params.get('location', '')
        date = params.get('date', '')
        
        if not all([location, date]):
            return {
                'error': 'Missing required activity parameters',
                'available': False
            }
        
        # Optional parameters
        activity_type = params.get('activity_type', '')
        participants = params.get('participants', 1)
        
        # In a real implementation, we would call an external activity booking API
        # For demonstration, we'll simulate the API call
        
        if AVAILABILITY_SYSTEM_URL:
            # Call external availability system
            response = call_availability_system('activity', params)
            return response
        else:
            # Simulate availability results
            return simulate_activity_availability(location, date, activity_type, participants)
        
    except Exception as e:
        logger.error(f"Error checking activity availability: {str(e)}")
        return {
            'error': f'Error checking activity availability: {str(e)}',
            'available': False
        }


def check_package_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check package (flight + hotel + activities) availability.
    
    Args:
        params: Package search parameters
        
    Returns:
        Dictionary with package availability results
    """
    try:
        logger.info(f"Checking package availability: {params}")
        
        # Extract component parameters
        flight_params = params.get('flight', {})
        hotel_params = params.get('hotel', {})
        activity_params = params.get('activities', [])
        
        # Check each component
        flight_results = check_flight_availability(flight_params) if flight_params else {}
        hotel_results = check_hotel_availability(hotel_params) if hotel_params else {}
        
        # Check activities if any
        activity_results = []
        for activity_param in activity_params:
            activity_result = check_activity_availability(activity_param)
            activity_results.append(activity_result)
        
        # Combine results
        package_results = {
            'flight': flight_results,
            'hotel': hotel_results,
            'activities': activity_results,
            'available': (
                flight_results.get('available', False) and
                hotel_results.get('available', False) and
                all(activity.get('available', False) for activity in activity_results)
                if activity_results else True
            )
        }
        
        return package_results
        
    except Exception as e:
        logger.error(f"Error checking package availability: {str(e)}")
        return {
            'error': f'Error checking package availability: {str(e)}',
            'available': False
        }


def call_availability_system(system_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call external availability system API.
    
    Args:
        system_type: Type of availability to check (flight, hotel, activity)
        params: Search parameters
        
    Returns:
        Response from the availability system
    """
    try:
        if not AVAILABILITY_SYSTEM_URL:
            raise ValueError("Availability system URL not configured")
        
        # Prepare the API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        
        payload = {
            'type': system_type,
            'params': params
        }
        
        # Make the API call
        response = requests.post(
            f"{AVAILABILITY_SYSTEM_URL}/check",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        # Process the response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error from availability system: {response.text}")
            return {
                'error': f"Availability system returned error: {response.status_code}",
                'available': False
            }
            
    except Exception as e:
        logger.error(f"Error calling availability system: {str(e)}")
        return {
            'error': f"Error calling availability system: {str(e)}",
            'available': False
        }


def check_loyalty_status(user_id: str) -> Dict[str, Any]:
    """
    Check user's loyalty program status.
    
    Args:
        user_id: User identifier
        
    Returns:
        Loyalty program information
    """
    try:
        if not LOYALTY_SYSTEM_URL:
            return {}
        
        # Prepare the API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        
        # Make the API call
        response = requests.get(
            f"{LOYALTY_SYSTEM_URL}/users/{user_id}/loyalty",
            headers=headers,
            timeout=5
        )
        
        # Process the response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error from loyalty system: {response.text}")
            return {}
            
    except Exception as e:
        logger.error(f"Error checking loyalty status: {str(e)}")
        return {}


# Simulation functions for demonstration purposes

def simulate_flight_availability(origin: str, destination: str, departure_date: str, 
                              return_date: str, passengers: int, cabin_class: str) -> Dict[str, Any]:
    """
    Simulate flight availability results for demonstration.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date
        return_date: Return date (if roundtrip)
        passengers: Number of passengers
        cabin_class: Cabin class (economy, premium, business, first)
        
    Returns:
        Simulated flight availability results
    """
    # Parse dates
    try:
        departure_dt = datetime.strptime(departure_date, '%Y-%m-%d')
        return_dt = datetime.strptime(return_date, '%Y-%m-%d') if return_date else None
    except ValueError:
        return {
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'available': False
        }
    
    # Generate flight options
    flight_options = []
    
    # Outbound flights
    for i in range(3):
        departure_time = departure_dt + timedelta(hours=i*4 + 8)
        arrival_time = departure_time + timedelta(hours=3)
        
        flight_options.append({
            'type': 'outbound',
            'airline': f"{'ABC' if i == 0 else 'XYZ'} Airlines",
            'flight_number': f"{'ABC' if i == 0 else 'XYZ'}{1000 + i}",
            'origin': origin,
            'destination': destination,
            'departure_time': departure_time.isoformat(),
            'arrival_time': arrival_time.isoformat(),
            'duration_minutes': 180,
            'cabin': cabin_class,
            'available_seats': 10 - i,
            'price': 250 + (i * 50) + (0 if cabin_class == 'economy' else 150)
        })
    
    # Return flights if roundtrip
    return_options = []
    if return_dt:
        for i in range(3):
            departure_time = return_dt + timedelta(hours=i*4 + 10)
            arrival_time = departure_time + timedelta(hours=3)
            
            return_options.append({
                'type': 'return',
                'airline': f"{'XYZ' if i == 0 else 'ABC'} Airlines",
                'flight_number': f"{'XYZ' if i == 0 else 'ABC'}{2000 + i}",
                'origin': destination,
                'destination': origin,
                'departure_time': departure_time.isoformat(),
                'arrival_time': arrival_time.isoformat(),
                'duration_minutes': 180,
                'cabin': cabin_class,
                'available_seats': 8 - i,
                'price': 280 + (i * 40) + (0 if cabin_class == 'economy' else 150)
            })
    
    return {
        'available': True,
        'origin': origin,
        'destination': destination,
        'outbound_flights': flight_options,
        'return_flights': return_options,
        'roundtrip': bool(return_date),
        'passengers': passengers,
        'cabin_class': cabin_class,
        'total_options': len(flight_options) * (len(return_options) if return_options else 1)
    }


def simulate_hotel_availability(location: str, check_in: str, check_out: str, 
                             rooms: int, guests: int, hotel_class: str) -> Dict[str, Any]:
    """
    Simulate hotel availability results for demonstration.
    
    Args:
        location: Location/city
        check_in: Check-in date
        check_out: Check-out date
        rooms: Number of rooms
        guests: Number of guests
        hotel_class: Hotel class/rating
        
    Returns:
        Simulated hotel availability results
    """
    # Parse dates
    try:
        check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
        stay_nights = (check_out_dt - check_in_dt).days
    except ValueError:
        return {
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'available': False
        }
    
    if stay_nights <= 0:
        return {
            'error': 'Check-out date must be after check-in date',
            'available': False
        }
    
    # Generate hotel options
    hotel_options = []
    
    # Sample hotel types based on class
    hotel_types = ['Luxury', 'Boutique', 'Resort', 'Standard']
    hotel_class_int = int(hotel_class) if hotel_class and hotel_class.isdigit() else 0
    
    for i in range(4):
        # Adjust hotel class if specified
        stars = min(5, max(1, (i + 2) if hotel_class_int == 0 else hotel_class_int))
        
        hotel_options.append({
            'name': f"{hotel_types[i]} Hotel {location}",
            'location': location,
            'address': f"{100 + i} Main Street, {location}",
            'stars': stars,
            'room_type': 'Standard' if i < 2 else 'Deluxe',
            'price_per_night': 100 + (stars * 30) + (i * 25),
            'total_price': (100 + (stars * 30) + (i * 25)) * stay_nights * rooms,
            'available_rooms': 5 - i,
            'amenities': [
                'WiFi', 
                'Breakfast' if i > 0 else None, 
                'Pool' if i > 1 else None, 
                'Spa' if i > 2 else None
            ],
            'cancellation_policy': 'Free cancellation' if i < 2 else 'Non-refundable'
        })
    
    return {
        'available': True,
        'location': location,
        'check_in': check_in,
        'check_out': check_out,
        'stay_nights': stay_nights,
        'rooms': rooms,
        'guests': guests,
        'hotels': hotel_options,
        'total_options': len(hotel_options)
    }


def simulate_activity_availability(location: str, date: str, 
                                activity_type: str, participants: int) -> Dict[str, Any]:
    """
    Simulate activity availability results for demonstration.
    
    Args:
        location: Location/city
        date: Activity date
        activity_type: Type of activity
        participants: Number of participants
        
    Returns:
        Simulated activity availability results
    """
    # Parse date
    try:
        activity_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'available': False
        }
    
    # Activity types and their properties
    activity_types = {
        'tour': {
            'name': 'City Guided Tour',
            'duration': 180,
            'price': 45
        },
        'museum': {
            'name': 'Museum Visit',
            'duration': 120,
            'price': 25
        },
        'adventure': {
            'name': 'Outdoor Adventure',
            'duration': 240,
            'price': 85
        },
        'culinary': {
            'name': 'Food Tasting Experience',
            'duration': 150,
            'price': 60
        }
    }
    
    # Default to 'tour' if not specified or invalid
    if not activity_type or activity_type not in activity_types:
        activity_type = 'tour'
    
    # Generate activity options
    activity_options = []
    
    # Get the specified activity type
    activity = activity_types[activity_type]
    
    # Add time options
    for i in range(3):
        start_time = activity_date.replace(hour=9 + i*3)
        end_time = start_time + timedelta(minutes=activity['duration'])
        
        activity_options.append({
            'name': activity['name'],
            'type': activity_type,
            'location': location,
            'date': date,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_minutes': activity['duration'],
            'price_per_person': activity['price'],
            'total_price': activity['price'] * participants,
            'available_spots': 20 - i*5,
            'language': 'English',
            'includes': ['Guide', 'Entrance fees'] if activity_type != 'adventure' else ['Equipment', 'Instructor', 'Safety gear']
        })
    
    # Add other activity types as options
    for other_type, other_activity in activity_types.items():
        if other_type != activity_type:
            start_time = activity_date.replace(hour=10)
            end_time = start_time + timedelta(minutes=other_activity['duration'])
            
            activity_options.append({
                'name': other_activity['name'],
                'type': other_type,
                'location': location,
                'date': date,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': other_activity['duration'],
                'price_per_person': other_activity['price'],
                'total_price': other_activity['price'] * participants,
                'available_spots': 15,
                'language': 'English',
                'includes': ['Guide', 'Entrance fees'] if other_type != 'adventure' else ['Equipment', 'Instructor', 'Safety gear']
            })
    
    return {
        'available': True,
        'location': location,
        'date': date,
        'activity_type': activity_type,
        'participants': participants,
        'activities': activity_options,
        'total_options': len(activity_options)
    }


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a formatted API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        API Gateway response object
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': json.dumps(body)
    }
