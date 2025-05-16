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
from utils.knowledge_base_client import KnowledgeBaseClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
bedrock_client = BedrockClient()
kb_client = KnowledgeBaseClient()

# Environment variables
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', '')
MODEL_ID = os.environ.get('IDEATION_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

def lambda_handler(event, context):
    """
    Lambda function handler for the Travel Ideation service.
    
    This function processes travel-related queries, generates ideas and recommendations
    based on the user's preferences, and augments these with knowledge from the 
    travel knowledge base.
    
    Args:
        event: API Gateway event or direct Lambda invocation event
        context: Lambda context
        
    Returns:
        Response with travel ideas and recommendations
    """
    try:
        logger.info("Processing ideation request")
        
        # Parse the request
        if event.get('body'):
            # API Gateway invocation
            body = json.loads(event.get('body', '{}'))
            query = body.get('query', '')
            user_preferences = body.get('preferences', {})
            context_data = body.get('context', {})
        else:
            # Direct Lambda invocation
            query = event.get('query', '')
            user_preferences = event.get('preferences', {})
            context_data = event.get('context', {})
        
        if not query:
            return create_response(400, {
                'error': 'Missing required parameter: query'
            })
        
        # Retrieve relevant knowledge
        kb_results = []
        if KNOWLEDGE_BASE_ID:
            logger.info(f"Retrieving knowledge for query: {query}")
            kb_results = kb_client.retrieve(query=query, max_results=3)
            logger.info(f"Retrieved {len(kb_results)} knowledge items")
        
        # Format the context from knowledge base
        knowledge_context = format_knowledge_context(kb_results)
        
        # Format user preferences for the prompt
        preferences_context = format_preferences(user_preferences)
        
        # Create the prompt for ideation
        prompt = create_ideation_prompt(query, preferences_context, knowledge_context)
        
        # Generate travel ideas using Bedrock
        logger.info("Generating travel ideas")
        ideas_response = bedrock_client.invoke_model(
            prompt=prompt,
            model_id=MODEL_ID,
            max_tokens=1500,
            temperature=0.7
        )
        
        # Parse the response to extract structured ideas
        ideas = parse_ideas_response(ideas_response)
        
        # Return the ideation results
        result = {
            'query': query,
            'ideas': ideas,
            'knowledge_used': bool(kb_results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Successfully generated travel ideas")
        
        # Check if this is an API Gateway or direct Lambda invocation
        if event.get('body'):
            # API Gateway response
            return create_response(200, result)
        else:
            # Direct Lambda invocation response
            return result
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        # Check if this is an API Gateway or direct Lambda invocation
        if event.get('body'):
            # API Gateway error response
            return create_response(500, {
                'error': f'Internal server error: {str(e)}'
            })
        else:
            # Direct Lambda invocation error response
            return {
                'error': f'Internal server error: {str(e)}'
            }


def create_ideation_prompt(query: str, preferences: str, knowledge: str) -> str:
    """
    Create a prompt for the ideation model.
    
    Args:
        query: User's travel query
        preferences: Formatted user preferences
        knowledge: Relevant knowledge from the knowledge base
        
    Returns:
        Formatted prompt for Bedrock
    """
    prompt = f"""
    You are a travel expert assistant specializing in generating creative and personalized travel ideas.
    
    USER QUERY:
    {query}
    
    USER PREFERENCES:
    {preferences}
    
    RELEVANT TRAVEL KNOWLEDGE:
    {knowledge}
    
    Please generate 3-5 specific travel ideas that address the user's query, taking into account their preferences.
    For each idea:
    1. Provide a title
    2. Write a brief description (2-3 sentences)
    3. List 2-3 key highlights or attractions
    4. Suggest an ideal duration for this experience
    
    Format your response as a structured list of ideas, with each idea having these components clearly labeled.
    Make your suggestions specific, actionable, and tailored to the context provided.
    """
    
    return prompt


def format_knowledge_context(kb_results: List[Dict[str, Any]]) -> str:
    """
    Format knowledge base results for inclusion in the prompt.
    
    Args:
        kb_results: Results from the knowledge base query
        
    Returns:
        Formatted knowledge context string
    """
    if not kb_results:
        return "No specific travel knowledge available."
    
    # Combine all the knowledge
    knowledge_text = "\n\n".join([
        f"- {result.get('content', '')}" for result in kb_results
    ])
    
    return knowledge_text


def format_preferences(preferences: Dict[str, Any]) -> str:
    """
    Format user preferences for inclusion in the prompt.
    
    Args:
        preferences: User preferences dictionary
        
    Returns:
        Formatted preferences string
    """
    if not preferences:
        return "No specific preferences provided."
    
    preference_items = []
    
    # Process known preference types
    if preferences.get('budget'):
        preference_items.append(f"Budget: {preferences['budget']}")
    
    if preferences.get('accommodation_type'):
        preference_items.append(f"Accommodation Type: {preferences['accommodation_type']}")
    
    if preferences.get('trip_duration'):
        preference_items.append(f"Trip Duration: {preferences['trip_duration']}")
    
    if preferences.get('interests'):
        interests = ", ".join(preferences['interests'])
        preference_items.append(f"Interests: {interests}")
    
    if preferences.get('travel_style'):
        preference_items.append(f"Travel Style: {preferences['travel_style']}")
    
    if preferences.get('dietary_restrictions'):
        dietary = ", ".join(preferences['dietary_restrictions'])
        preference_items.append(f"Dietary Restrictions: {dietary}")
    
    # Add any other preferences as generic items
    for key, value in preferences.items():
        if key not in ['budget', 'accommodation_type', 'trip_duration', 'interests', 'travel_style', 'dietary_restrictions']:
            if isinstance(value, list):
                value_str = ", ".join(value)
                preference_items.append(f"{key.replace('_', ' ').title()}: {value_str}")
            else:
                preference_items.append(f"{key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(preference_items)


def parse_ideas_response(response: str) -> List[Dict[str, Any]]:
    """
    Parse the ideation model response into structured data.
    
    This is a simple implementation. In a production system, you would
    use more robust parsing or explicitly ask the model to return JSON.
    
    Args:
        response: Raw model response text
        
    Returns:
        List of structured idea objects
    """
    try:
        # Simple parsing based on expected format
        ideas = []
        current_idea = None
        
        for line in response.strip().split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for idea title pattern (assuming numbered list)
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) and ':' in line:
                # If we already have an idea in progress, save it
                if current_idea and current_idea.get('title'):
                    ideas.append(current_idea)
                
                # Start a new idea
                title_parts = line.split(':', 1)
                current_idea = {
                    'title': title_parts[1].strip() if len(title_parts) > 1 else line,
                    'description': '',
                    'highlights': [],
                    'duration': ''
                }
            
            # Check for labeled components
            elif current_idea:
                if line.lower().startswith('description:'):
                    current_idea['description'] = line.split(':', 1)[1].strip()
                elif line.lower().startswith('highlight'):
                    highlight = line.split(':', 1)[1].strip() if ':' in line else line
                    current_idea['highlights'].append(highlight)
                elif line.lower().startswith('duration:'):
                    current_idea['duration'] = line.split(':', 1)[1].strip()
                # Add more content to description if no specific label is found
                elif current_idea['description'] and not line.startswith('-'):
                    current_idea['description'] += ' ' + line
                # If it's a bullet point, assume it's a highlight
                elif line.startswith('-'):
                    highlight = line[1:].strip()
                    current_idea['highlights'].append(highlight)
        
        # Don't forget to add the last idea
        if current_idea and current_idea.get('title'):
            ideas.append(current_idea)
        
        # If we couldn't parse structured data, return the raw response
        if not ideas:
            return [{
                'title': 'Travel Recommendations',
                'description': response.strip(),
                'highlights': [],
                'duration': ''
            }]
        
        return ideas
        
    except Exception as e:
        logger.error(f"Error parsing ideas response: {str(e)}")
        # Fallback to returning raw response
        return [{
            'title': 'Travel Recommendations',
            'description': response.strip(),
            'highlights': [],
            'duration': ''
        }]


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
