import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils.bedrock_client import BedrockClient
from utils.s3_client import S3Client
from utils.knowledge_base_client import KnowledgeBaseClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
bedrock_client = BedrockClient()
s3_client = S3Client()
kb_client = KnowledgeBaseClient()

# Environment variables
MODEL_ID = os.environ.get('QA_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

def lambda_handler(event, context):
    """
    Lambda function handler for the Bookings Q&A service.
    
    This function processes questions about existing bookings, retrieves the relevant
    booking data, and provides detailed answers using Bedrock's generative capabilities.
    
    Args:
        event: API Gateway event or direct Lambda invocation
        context: Lambda context
        
    Returns:
        Response with booking information
    """
    try:
        logger.info("Processing bookings Q&A request")
        
        # Parse the request
        if event.get('body'):
            # API Gateway invocation
            body = json.loads(event.get('body', '{}'))
            query = body.get('query', '')
            user_id = body.get('user_id', '')
            booking_id = body.get('booking_id', '')
        else:
            # Direct Lambda invocation
            query = event.get('query', '')
            user_id = event.get('user_id', '')
            booking_id = event.get('booking_id', '')
        
        if not query:
            return create_response(400, {
                'error': 'Missing required parameter: query'
            })
        
        if not (user_id or booking_id):
            return create_response(400, {
                'error': 'Missing required parameter: either user_id or booking_id must be provided'
            })
        
        # Retrieve booking data
        booking_data = []
        if booking_id:
            # Retrieve specific booking by ID
            booking = s3_client.get_booking_data(booking_id)
            if booking:
                booking_data.append(booking)
        elif user_id:
            # Retrieve all bookings for a user
            # In a real implementation, you would have a database query or index search
            # For our simulation, we'll list S3 objects and filter by user ID
            booking_objects = s3_client.list_objects(s3_client.bookings_bucket, 'bookings/')
            
            for obj in booking_objects:
                booking = s3_client.get_object(s3_client.bookings_bucket, obj.get('key', ''))
                if booking.get('data'):
                    booking_json = json.loads(booking.get('data', '{}'))
                    if booking_json.get('user_info', {}).get('id') == user_id:
                        booking_data.append(booking_json)
        
        if not booking_data:
            return create_response(404, {
                'error': 'No booking data found',
                'answer': 'I could not find any booking information with the provided details.'
            })
        
        # Format the booking data for the context
        booking_context = format_booking_context(booking_data)
        
        # Create the prompt for the Q&A model
        prompt = create_qa_prompt(query, booking_context)
        
        # Generate the answer using Bedrock
        logger.info("Generating answer with Bedrock")
        answer = bedrock_client.invoke_model(
            prompt=prompt,
            model_id=MODEL_ID,
            max_tokens=1000,
            temperature=0.2  # Lower temperature for more factual responses
        )
        
        # Return the Q&A result
        result = {
            'query': query,
            'answer': answer,
            'booking_count': len(booking_data),
            'has_booking_data': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Successfully generated answer for booking query")
        
        # Return based on invocation type
        if event.get('body'):
            return create_response(200, result)
        else:
            return result
        
    except Exception as e:
        logger.error(f"Error processing bookings Q&A request: {str(e)}")
        error_message = f'Internal server error: {str(e)}'
        error_response = {
            'error': error_message,
            'answer': 'I apologize, but I encountered an error while retrieving your booking information.'
        }
        
        if event.get('body'):
            return create_response(500, error_response)
        else:
            return error_response


def create_qa_prompt(query: str, booking_context: str) -> str:
    """
    Create a prompt for the Q&A model.
    
    Args:
        query: User's question about bookings
        booking_context: Formatted booking information
        
    Returns:
        Formatted prompt for Bedrock
    """
    prompt = f"""
    You are a helpful travel assistant specializing in providing accurate information about customer bookings.
    
    USER QUERY:
    {query}
    
    BOOKING INFORMATION:
    {booking_context}
    
    Please answer the user's question based on the booking information provided above.
    Be specific, factual, and only use the information provided.
    If the answer is not explicitly found in the booking information, acknowledge this and suggest what information might be needed.
    If the query is about changing or cancelling a booking, explain the general policy but advise the user to contact customer service for specific actions.
    Format any dates, times, and monetary values clearly.
    """
    
    return prompt


def format_booking_context(bookings: List[Dict[str, Any]]) -> str:
    """
    Format booking data for inclusion in the prompt.
    
    Args:
        bookings: List of booking data
        
    Returns:
        Formatted booking context string
    """
    if not bookings:
        return "No booking information available."
    
    context_parts = []
    
    for i, booking in enumerate(bookings):
        booking_type = booking.get('booking_type', 'unknown').lower()
        details = booking.get('details', {})
        confirmation = booking.get('confirmation', {})
        
        booking_info = [f"BOOKING {i+1}:"]
        booking_info.append(f"Booking ID: {booking.get('booking_id', 'unknown')}")
        booking_info.append(f"Type: {booking_type.capitalize()}")
        booking_info.append(f"Status: {booking.get('status', 'unknown')}")
        booking_info.append(f"Booking Date: {booking.get('timestamp', 'unknown')}")
        
        if confirmation:
            if 'confirmation_code' in confirmation:
                booking_info.append(f"Confirmation Code: {confirmation.get('confirmation_code', 'unknown')}")
            
            if 'total_amount' in confirmation:
                booking_info.append(f"Total Amount: ${confirmation.get('total_amount', 0)} {confirmation.get('currency', 'USD')}")
        
        # Add type-specific details
        if booking_type == 'flight':
            if confirmation:
                booking_info.append(f"Airline: {confirmation.get('airline', 'unknown')}")
                booking_info.append(f"Flight Number: {confirmation.get('flight_number', 'unknown')}")
                booking_info.append(f"Departure Date: {confirmation.get('departure_date', 'unknown')}")
                booking_info.append(f"Cabin Class: {confirmation.get('cabin_class', 'unknown')}")
                booking_info.append(f"Passengers: {confirmation.get('passenger_count', 0)}")
            elif details:
                booking_info.append(f"Flight ID: {details.get('flight_id', 'unknown')}")
                booking_info.append(f"Passengers: {len(details.get('passengers', []))}")
        
        elif booking_type == 'hotel':
            if confirmation:
                booking_info.append(f"Hotel: {confirmation.get('hotel_name', 'unknown')}")
                booking_info.append(f"Location: {confirmation.get('location', 'unknown')}")
                booking_info.append(f"Room Type: {confirmation.get('room_type', 'unknown')}")
                booking_info.append(f"Check-in: {confirmation.get('check_in', 'unknown')}")
                booking_info.append(f"Check-out: {confirmation.get('check_out', 'unknown')}")
                booking_info.append(f"Nights: {confirmation.get('nights', 0)}")
                booking_info.append(f"Guests: {confirmation.get('guests', 0)}")
            elif details:
                booking_info.append(f"Hotel ID: {details.get('hotel_id', 'unknown')}")
                booking_info.append(f"Room Type: {details.get('room_type', 'unknown')}")
                booking_info.append(f"Check-in: {details.get('check_in', 'unknown')}")
                booking_info.append(f"Check-out: {details.get('check_out', 'unknown')}")
                booking_info.append(f"Guests: {len(details.get('guests', []))}")
        
        elif booking_type == 'activity':
            if confirmation:
                booking_info.append(f"Activity: {confirmation.get('activity_name', 'unknown')}")
                booking_info.append(f"Type: {confirmation.get('activity_type', 'unknown')}")
                booking_info.append(f"Location: {confirmation.get('location', 'unknown')}")
                booking_info.append(f"Date: {confirmation.get('date', 'unknown')}")
                booking_info.append(f"Time: {confirmation.get('time_slot', 'unknown')}")
                booking_info.append(f"Participants: {confirmation.get('participants', 0)}")
            elif details:
                booking_info.append(f"Activity ID: {details.get('activity_id', 'unknown')}")
                booking_info.append(f"Date: {details.get('date', 'unknown')}")
                booking_info.append(f"Time: {details.get('time_slot', 'unknown')}")
                booking_info.append(f"Participants: {len(details.get('participants', []))}")
        
        elif booking_type == 'package':
            booking_info.append("Package Components:")
            
            if 'flight' in confirmation:
                flight = confirmation.get('flight', {})
                booking_info.append("  Flight:")
                booking_info.append(f"  - Airline: {flight.get('airline', 'unknown')}")
                booking_info.append(f"  - Flight Number: {flight.get('flight_number', 'unknown')}")
                booking_info.append(f"  - Departure Date: {flight.get('departure_date', 'unknown')}")
            
            if 'hotel' in confirmation:
                hotel = confirmation.get('hotel', {})
                booking_info.append("  Hotel:")
                booking_info.append(f"  - Name: {hotel.get('hotel_name', 'unknown')}")
                booking_info.append(f"  - Check-in: {hotel.get('check_in', 'unknown')}")
                booking_info.append(f"  - Check-out: {hotel.get('check_out', 'unknown')}")
            
            if 'activities' in confirmation:
                activities = confirmation.get('activities', [])
                if activities:
                    booking_info.append("  Activities:")
                    for i, activity in enumerate(activities):
                        booking_info.append(f"  - Activity {i+1}: {activity.get('activity_name', 'unknown')} on {activity.get('date', 'unknown')}")
        
        context_parts.append("\n".join(booking_info))
    
    return "\n\n".join(context_parts)


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
