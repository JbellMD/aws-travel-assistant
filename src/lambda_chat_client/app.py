import os
import json
import uuid
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils.bedrock_client import BedrockClient
from utils.knowledge_base_client import KnowledgeBaseClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
bedrock_client = BedrockClient()
kb_client = KnowledgeBaseClient()

# Environment variables
GUARDRAILS_AGENT_ID = os.environ.get('GUARDRAILS_AGENT_ID', '')
GUARDRAILS_AGENT_ALIAS_ID = os.environ.get('GUARDRAILS_AGENT_ALIAS_ID', '')


def lambda_handler(event, context):
    """
    Lambda function handler for the Chat Client API.
    
    This function processes chat messages from users, routes them through
    Bedrock Guardrails for content filtering, and returns appropriate responses.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        logger.info("Processing chat request")
        
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        message = body.get('message', '')
        session_id = body.get('session_id', '')
        user_id = body.get('user_id', '')
        
        if not message:
            return create_response(400, {
                'error': 'Missing required parameter: message'
            })
        
        # Generate a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        
        # Create conversation context
        conversation_context = create_conversation_context(user_id, session_id)
        
        # Process the message through Guardrails if configured
        if GUARDRAILS_AGENT_ID and GUARDRAILS_AGENT_ALIAS_ID:
            logger.info(f"Routing message through Guardrails agent {GUARDRAILS_AGENT_ID}")
            
            # Call Bedrock Guardrails
            guardrails_response = bedrock_client.invoke_agent(
                agent_id=GUARDRAILS_AGENT_ID,
                agent_alias_id=GUARDRAILS_AGENT_ALIAS_ID,
                input_text=message,
                session_id=session_id
            )
            
            response_text = guardrails_response.get('completion', '')
            
            # Check if response indicates unsafe content
            if "I apologize, but I cannot" in response_text or "I'm unable to" in response_text:
                logger.warning("Message flagged by guardrails")
                return create_response(200, {
                    'message': response_text,
                    'session_id': session_id,
                    'flagged': True
                })
                
            logger.info("Message passed guardrails check")
        else:
            # No guardrails configured, route directly to Lambda ideation function
            response_text = "No guardrails configured. Please configure Bedrock Guardrails for content filtering."
            logger.warning("No guardrails configured, using fallback response")
        
        # In the real implementation, we would now call another Lambda function 
        # for further processing (ideation, booking, etc.)
        # For now, just return a mock response
        
        return create_response(200, {
            'message': response_text or "I understand you're interested in travel. Let me help you plan your trip.",
            'session_id': session_id,
            'context': conversation_context
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {
            'error': f'Internal server error: {str(e)}'
        })


def create_conversation_context(user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Create a conversation context object with user and session information.
    
    In a real implementation, this would retrieve user preferences, past bookings,
    and other context to personalize the conversation.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Dictionary with conversation context
    """
    # Basic context
    context = {
        'timestamp': datetime.utcnow().isoformat(),
        'session_id': session_id,
        'user': {
            'id': user_id
        }
    }
    
    # In a real implementation, we would retrieve user preferences, 
    # booking history, etc. from a database or other services
    
    return context


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
