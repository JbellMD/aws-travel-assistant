import os
import json
import logging
import sys
import uuid
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils.bedrock_client import BedrockClient
from utils.s3_client import S3Client

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
bedrock_client = BedrockClient()
s3_client = S3Client()

# Environment variables for external systems
BOOKING_SYSTEM_URL = os.environ.get('BOOKING_SYSTEM_URL', '')
LOYALTY_SYSTEM_URL = os.environ.get('LOYALTY_SYSTEM_URL', '')
API_KEY = os.environ.get('EXTERNAL_API_KEY', '')

def lambda_handler(event, context):
    """
    Lambda function handler for processing travel bookings.
    
    This function processes booking requests, makes reservations in external systems,
    and stores booking data for future reference.
    
    Args:
        event: API Gateway event or direct Lambda invocation
        context: Lambda context
        
    Returns:
        Booking confirmation details
    """
    try:
        logger.info("Processing booking request")
        
        # Parse the request
        if event.get('body'):
            # API Gateway invocation
            body = json.loads(event.get('body', '{}'))
            booking_type = body.get('type', '')
            booking_details = body.get('details', {})
            user_info = body.get('user_info', {})
            payment_info = body.get('payment_info', {})
        else:
            # Direct Lambda invocation
            booking_type = event.get('type', '')
            booking_details = event.get('details', {})
            user_info = event.get('user_info', {})
            payment_info = event.get('payment_info', {})
        
        # Validate required parameters
        if not booking_type:
            return create_response(400, {
                'error': 'Missing required parameter: type'
            })
        
        if not booking_details:
            return create_response(400, {
                'error': 'Missing required parameter: details'
            })
        
        if not user_info:
            return create_response(400, {
                'error': 'Missing required parameter: user_info'
            })
        
        # Generate a unique booking ID
        booking_id = str(uuid.uuid4())
        
        # Process the booking based on type
        booking_result = {}
        if booking_type.lower() == 'flight':
            booking_result = process_flight_booking(booking_id, booking_details, user_info, payment_info)
        elif booking_type.lower() == 'hotel':
            booking_result = process_hotel_booking(booking_id, booking_details, user_info, payment_info)
        elif booking_type.lower() == 'activity':
            booking_result = process_activity_booking(booking_id, booking_details, user_info, payment_info)
        elif booking_type.lower() == 'package':
            booking_result = process_package_booking(booking_id, booking_details, user_info, payment_info)
        else:
            return create_response(400, {
                'error': f'Unsupported booking type: {booking_type}'
            })
        
        # Check for errors in booking result
        if 'error' in booking_result:
            return create_response(400, booking_result)
        
        # Store the booking information in S3
        booking_data = {
            'booking_id': booking_id,
            'booking_type': booking_type,
            'details': booking_details,
            'user_info': user_info,
            'timestamp': datetime.utcnow().isoformat(),
            'status': booking_result.get('status', 'confirmed'),
            'confirmation': booking_result
        }
        
        s3_client.save_booking_data(booking_id, booking_data)
        
        # Add loyalty points if applicable
        if user_info.get('id') and LOYALTY_SYSTEM_URL:
            add_loyalty_points(user_info.get('id'), booking_type, booking_result.get('total_amount', 0))
        
        # Return the booking confirmation
        result = {
            'booking_id': booking_id,
            'status': booking_result.get('status', 'confirmed'),
            'timestamp': datetime.utcnow().isoformat(),
            'confirmation': booking_result
        }
        
        logger.info(f"Successfully processed {booking_type} booking: {booking_id}")
        
        # Return based on invocation type
        if event.get('body'):
            return create_response(200, result)
        else:
            return result
        
    except Exception as e:
        logger.error(f"Error processing booking request: {str(e)}")
        error_response = {
            'error': f'Internal server error: {str(e)}'
        }
        
        if event.get('body'):
            return create_response(500, error_response)
        else:
            return error_response


def process_flight_booking(booking_id: str, details: Dict[str, Any], 
                         user_info: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a flight booking request.
    
    Args:
        booking_id: Unique booking identifier
        details: Flight booking details
        user_info: User information
        payment_info: Payment information
        
    Returns:
        Booking confirmation details
    """
    try:
        logger.info(f"Processing flight booking: {booking_id}")
        
        # Required flight parameters
        flight_id = details.get('flight_id', '')
        passengers = details.get('passengers', [])
        
        if not flight_id:
            return {
                'error': 'Missing required parameter: flight_id'
            }
        
        if not passengers:
            return {
                'error': 'Missing required parameter: passengers'
            }
        
        # In a real implementation, we would call an external flight booking API
        # For demonstration, we'll simulate the booking process
        
        if BOOKING_SYSTEM_URL:
            # Call external booking system
            booking_details = {
                'booking_id': booking_id,
                'flight_id': flight_id,
                'passengers': passengers,
                'user_info': user_info,
                'payment_info': payment_info
            }
            
            response = call_booking_system('flight', booking_details)
            return response
        else:
            # Simulate booking confirmation
            return simulate_flight_booking(booking_id, flight_id, passengers, user_info)
        
    except Exception as e:
        logger.error(f"Error processing flight booking: {str(e)}")
        return {
            'error': f'Error processing flight booking: {str(e)}'
        }


def process_hotel_booking(booking_id: str, details: Dict[str, Any], 
                        user_info: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a hotel booking request.
    
    Args:
        booking_id: Unique booking identifier
        details: Hotel booking details
        user_info: User information
        payment_info: Payment information
        
    Returns:
        Booking confirmation details
    """
    try:
        logger.info(f"Processing hotel booking: {booking_id}")
        
        # Required hotel parameters
        hotel_id = details.get('hotel_id', '')
        room_type = details.get('room_type', '')
        check_in = details.get('check_in', '')
        check_out = details.get('check_out', '')
        guests = details.get('guests', [])
        
        if not all([hotel_id, room_type, check_in, check_out]):
            return {
                'error': 'Missing required hotel parameters'
            }
        
        if not guests:
            return {
                'error': 'Missing required parameter: guests'
            }
        
        # In a real implementation, we would call an external hotel booking API
        # For demonstration, we'll simulate the booking process
        
        if BOOKING_SYSTEM_URL:
            # Call external booking system
            booking_details = {
                'booking_id': booking_id,
                'hotel_id': hotel_id,
                'room_type': room_type,
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests,
                'user_info': user_info,
                'payment_info': payment_info
            }
            
            response = call_booking_system('hotel', booking_details)
            return response
        else:
            # Simulate booking confirmation
            return simulate_hotel_booking(booking_id, hotel_id, room_type, check_in, check_out, guests, user_info)
        
    except Exception as e:
        logger.error(f"Error processing hotel booking: {str(e)}")
        return {
            'error': f'Error processing hotel booking: {str(e)}'
        }


def process_activity_booking(booking_id: str, details: Dict[str, Any], 
                          user_info: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an activity booking request.
    
    Args:
        booking_id: Unique booking identifier
        details: Activity booking details
        user_info: User information
        payment_info: Payment information
        
    Returns:
        Booking confirmation details
    """
    try:
        logger.info(f"Processing activity booking: {booking_id}")
        
        # Required activity parameters
        activity_id = details.get('activity_id', '')
        date = details.get('date', '')
        time_slot = details.get('time_slot', '')
        participants = details.get('participants', [])
        
        if not all([activity_id, date, time_slot]):
            return {
                'error': 'Missing required activity parameters'
            }
        
        if not participants:
            return {
                'error': 'Missing required parameter: participants'
            }
        
        # In a real implementation, we would call an external activity booking API
        # For demonstration, we'll simulate the booking process
        
        if BOOKING_SYSTEM_URL:
            # Call external booking system
            booking_details = {
                'booking_id': booking_id,
                'activity_id': activity_id,
                'date': date,
                'time_slot': time_slot,
                'participants': participants,
                'user_info': user_info,
                'payment_info': payment_info
            }
            
            response = call_booking_system('activity', booking_details)
            return response
        else:
            # Simulate booking confirmation
            return simulate_activity_booking(booking_id, activity_id, date, time_slot, participants, user_info)
        
    except Exception as e:
        logger.error(f"Error processing activity booking: {str(e)}")
        return {
            'error': f'Error processing activity booking: {str(e)}'
        }


def process_package_booking(booking_id: str, details: Dict[str, Any], 
                         user_info: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a package (flight + hotel + activities) booking request.
    
    Args:
        booking_id: Unique booking identifier
        details: Package booking details
        user_info: User information
        payment_info: Payment information
        
    Returns:
        Booking confirmation details
    """
    try:
        logger.info(f"Processing package booking: {booking_id}")
        
        # Extract component details
        flight_details = details.get('flight', {})
        hotel_details = details.get('hotel', {})
        activity_details = details.get('activities', [])
        
        # Process each component
        flight_result = process_flight_booking(f"{booking_id}-flight", flight_details, user_info, payment_info) if flight_details else {}
        hotel_result = process_hotel_booking(f"{booking_id}-hotel", hotel_details, user_info, payment_info) if hotel_details else {}
        
        # Process activities if any
        activity_results = []
        for i, activity_detail in enumerate(activity_details):
            activity_result = process_activity_booking(f"{booking_id}-activity-{i+1}", activity_detail, user_info, payment_info)
            activity_results.append(activity_result)
        
        # Check for errors in any component
        if 'error' in flight_result or 'error' in hotel_result or any('error' in result for result in activity_results):
            error_messages = []
            if 'error' in flight_result:
                error_messages.append(f"Flight: {flight_result['error']}")
            if 'error' in hotel_result:
                error_messages.append(f"Hotel: {hotel_result['error']}")
            for i, result in enumerate(activity_results):
                if 'error' in result:
                    error_messages.append(f"Activity {i+1}: {result['error']}")
            
            return {
                'error': f"Package booking failed: {'; '.join(error_messages)}"
            }
        
        # Combine results
        total_amount = (
            flight_result.get('total_amount', 0) +
            hotel_result.get('total_amount', 0) +
            sum(result.get('total_amount', 0) for result in activity_results)
        )
        
        package_result = {
            'booking_id': booking_id,
            'status': 'confirmed',
            'flight': flight_result,
            'hotel': hotel_result,
            'activities': activity_results,
            'total_amount': total_amount,
            'currency': 'USD',
            'booking_date': datetime.utcnow().isoformat(),
            'confirmation_code': f"PKG-{booking_id[:8].upper()}"
        }
        
        return package_result
        
    except Exception as e:
        logger.error(f"Error processing package booking: {str(e)}")
        return {
            'error': f'Error processing package booking: {str(e)}'
        }


def call_booking_system(booking_type: str, booking_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call external booking system API.
    
    Args:
        booking_type: Type of booking (flight, hotel, activity)
        booking_details: Booking details
        
    Returns:
        Response from the booking system
    """
    try:
        if not BOOKING_SYSTEM_URL:
            raise ValueError("Booking system URL not configured")
        
        # Prepare the API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        
        payload = {
            'type': booking_type,
            'details': booking_details
        }
        
        # Make the API call
        response = requests.post(
            f"{BOOKING_SYSTEM_URL}/book",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        # Process the response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error from booking system: {response.text}")
            return {
                'error': f"Booking system returned error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error calling booking system: {str(e)}")
        return {
            'error': f"Error calling booking system: {str(e)}"
        }


def add_loyalty_points(user_id: str, booking_type: str, amount: float) -> bool:
    """
    Add loyalty points for a booking.
    
    Args:
        user_id: User identifier
        booking_type: Type of booking
        amount: Booking amount
        
    Returns:
        Boolean indicating success
    """
    try:
        if not LOYALTY_SYSTEM_URL:
            logger.info("Loyalty system URL not configured, skipping points")
            return False
        
        # Calculate points based on booking type and amount
        points = int(amount * 0.1)  # 1 point per $10 spent
        if booking_type.lower() == 'flight':
            points = int(amount * 0.2)  # 2 points per $10 for flights
        
        # Prepare the API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        
        payload = {
            'user_id': user_id,
            'points': points,
            'activity': f"{booking_type.capitalize()} Booking",
            'amount': amount
        }
        
        # Make the API call
        response = requests.post(
            f"{LOYALTY_SYSTEM_URL}/points/add",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        # Process the response
        if response.status_code == 200:
            logger.info(f"Successfully added {points} loyalty points for user {user_id}")
            return True
        else:
            logger.error(f"Error adding loyalty points: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding loyalty points: {str(e)}")
        return False


# Simulation functions for demonstration purposes

def simulate_flight_booking(booking_id: str, flight_id: str, 
                         passengers: List[Dict[str, Any]], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate flight booking confirmation for demonstration.
    
    Args:
        booking_id: Booking identifier
        flight_id: Flight identifier
        passengers: List of passenger details
        user_info: User information
        
    Returns:
        Simulated booking confirmation
    """
    # Extract flight details from ID (format: AIRLINE-FLIGHTNUM-DATE-CLASS)
    flight_parts = flight_id.split('-')
    if len(flight_parts) < 4:
        return {
            'error': 'Invalid flight ID format'
        }
    
    airline = flight_parts[0]
    flight_number = flight_parts[1]
    flight_date = flight_parts[2]
    cabin_class = flight_parts[3]
    
    # Calculate price based on passengers and class
    base_price = 250
    if cabin_class.lower() == 'business':
        base_price = 750
    elif cabin_class.lower() == 'first':
        base_price = 1200
    
    passenger_count = len(passengers)
    total_amount = base_price * passenger_count
    
    # Generate booking confirmation
    return {
        'booking_id': booking_id,
        'status': 'confirmed',
        'airline': airline,
        'flight_number': flight_number,
        'departure_date': flight_date,
        'cabin_class': cabin_class,
        'passengers': passenger_count,
        'passenger_names': [p.get('name', '') for p in passengers],
        'total_amount': total_amount,
        'currency': 'USD',
        'booking_date': datetime.utcnow().isoformat(),
        'confirmation_code': f"AIR-{booking_id[:8].upper()}"
    }


def simulate_hotel_booking(booking_id: str, hotel_id: str, room_type: str, 
                        check_in: str, check_out: str, guests: List[Dict[str, Any]], 
                        user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate hotel booking confirmation for demonstration.
    
    Args:
        booking_id: Booking identifier
        hotel_id: Hotel identifier
        room_type: Room type
        check_in: Check-in date
        check_out: Check-out date
        guests: List of guest details
        user_info: User information
        
    Returns:
        Simulated booking confirmation
    """
    # Parse dates to calculate number of nights
    try:
        check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
        nights = (check_out_dt - check_in_dt).days
    except ValueError:
        return {
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }
    
    if nights <= 0:
        return {
            'error': 'Check-out date must be after check-in date'
        }
    
    # Extract hotel details from ID (format: HOTEL-LOCATION-STARS)
    hotel_parts = hotel_id.split('-')
    if len(hotel_parts) < 3:
        return {
            'error': 'Invalid hotel ID format'
        }
    
    hotel_name = hotel_parts[0]
    location = hotel_parts[1]
    stars = int(hotel_parts[2]) if hotel_parts[2].isdigit() else 3
    
    # Calculate price based on room type, stars, and nights
    base_price = 100 + (stars * 30)
    if room_type.lower() == 'deluxe':
        base_price += 50
    elif room_type.lower() == 'suite':
        base_price += 150
    
    total_amount = base_price * nights
    
    # Generate booking confirmation
    return {
        'booking_id': booking_id,
        'status': 'confirmed',
        'hotel_name': hotel_name,
        'location': location,
        'stars': stars,
        'room_type': room_type,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'guests': len(guests),
        'guest_names': [g.get('name', '') for g in guests],
        'total_amount': total_amount,
        'currency': 'USD',
        'booking_date': datetime.utcnow().isoformat(),
        'confirmation_code': f"HTL-{booking_id[:8].upper()}"
    }


def simulate_activity_booking(booking_id: str, activity_id: str, date: str, 
                           time_slot: str, participants: List[Dict[str, Any]], 
                           user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate activity booking confirmation for demonstration.
    
    Args:
        booking_id: Booking identifier
        activity_id: Activity identifier
        date: Activity date
        time_slot: Time slot
        participants: List of participant details
        user_info: User information
        
    Returns:
        Simulated booking confirmation
    """
    # Extract activity details from ID (format: ACTIVITY-TYPE-LOCATION)
    activity_parts = activity_id.split('-')
    if len(activity_parts) < 3:
        return {
            'error': 'Invalid activity ID format'
        }
    
    activity_name = activity_parts[0]
    activity_type = activity_parts[1]
    location = activity_parts[2]
    
    # Calculate price based on activity type and participants
    base_price = 0
    if activity_type.lower() == 'tour':
        base_price = 45
    elif activity_type.lower() == 'museum':
        base_price = 25
    elif activity_type.lower() == 'adventure':
        base_price = 85
    elif activity_type.lower() == 'culinary':
        base_price = 60
    else:
        base_price = 50
    
    participant_count = len(participants)
    total_amount = base_price * participant_count
    
    # Generate booking confirmation
    return {
        'booking_id': booking_id,
        'status': 'confirmed',
        'activity_name': activity_name,
        'activity_type': activity_type,
        'location': location,
        'date': date,
        'time_slot': time_slot,
        'participants': participant_count,
        'participant_names': [p.get('name', '') for p in participants],
        'total_amount': total_amount,
        'currency': 'USD',
        'booking_date': datetime.utcnow().isoformat(),
        'confirmation_code': f"ACT-{booking_id[:8].upper()}"
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
