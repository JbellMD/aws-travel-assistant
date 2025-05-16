import os
import json
import boto3
import logging
from typing import Dict, Any, List, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BedrockClient:
    """
    Utility class for interacting with Amazon Bedrock services.
    Handles both model invocation and agent interactions.
    """
    
    def __init__(self, region_name: str = None):
        """
        Initialize the Bedrock client.
        
        Args:
            region_name: AWS region where Bedrock is deployed
        """
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize Bedrock Runtime client for model invocations
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )
        
        # Initialize Bedrock Agent Runtime client for agent interactions
        self.bedrock_agent_runtime = boto3.client(
            service_name='bedrock-agent-runtime',
            region_name=self.region_name
        )
        
        # Default model IDs
        self.default_text_model = os.environ.get('DEFAULT_TEXT_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')
        self.default_embedding_model = os.environ.get('DEFAULT_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
        
        logger.info(f"Initialized Bedrock client in region {self.region_name}")
    
    def invoke_model(self, 
                     prompt: str, 
                     model_id: str = None, 
                     max_tokens: int = 1000, 
                     temperature: float = 0.7) -> str:
        """
        Invoke a Bedrock model with the given prompt.
        
        Args:
            prompt: The input prompt
            model_id: The model ID to use (defaults to environment variable)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            The generated text response
        """
        model_id = model_id or self.default_text_model
        logger.info(f"Invoking model {model_id}")
        
        try:
            # Format the request body based on the model type
            if model_id.startswith('anthropic.claude'):
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            elif model_id.startswith('amazon.titan'):
                request_body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": 0.9
                    }
                }
            else:
                logger.warning(f"Unsupported model: {model_id}, using generic format")
                request_body = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            
            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response based on model type
            response_body = json.loads(response['body'].read().decode('utf-8'))
            
            if model_id.startswith('anthropic.claude'):
                generated_text = response_body.get('content', [{}])[0].get('text', '')
            elif model_id.startswith('amazon.titan'):
                generated_text = response_body.get('results', [{}])[0].get('outputText', '')
            else:
                generated_text = str(response_body)
                
            logger.info("Successfully generated response")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error invoking model: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def create_embeddings(self, text: str, model_id: str = None) -> List[float]:
        """
        Generate embeddings for the input text.
        
        Args:
            text: The input text to generate embeddings for
            model_id: The embedding model ID to use
            
        Returns:
            The generated embedding vector
        """
        model_id = model_id or self.default_embedding_model
        
        try:
            logger.info(f"Creating embeddings with model: {model_id}")
            
            # Prepare the request body
            request_body = {
                "inputText": text
            }
            
            # Call the Bedrock embedding model
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            
            # Extract embeddings from the response
            embeddings = response_body.get('embedding', [])
            
            logger.info(f"Successfully generated embeddings with dimension: {len(embeddings)}")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []
    
    def invoke_agent(self, 
                    agent_id: str, 
                    agent_alias_id: str, 
                    input_text: str, 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke a Bedrock Agent with the given input.
        
        Args:
            agent_id: The Bedrock Agent ID
            agent_alias_id: The Agent Alias ID
            input_text: The input text for the agent
            session_id: Optional session ID for maintaining conversation context
            
        Returns:
            The agent response
        """
        try:
            logger.info(f"Invoking agent {agent_id} with alias {agent_alias_id}")
            
            # Prepare the request
            request_params = {
                'agentId': agent_id,
                'agentAliasId': agent_alias_id,
                'inputText': input_text
            }
            
            # Add session ID if provided
            if session_id:
                request_params['sessionId'] = session_id
            
            # Invoke the agent
            response = self.bedrock_agent_runtime.invoke_agent(**request_params)
            
            logger.info("Successfully invoked agent")
            return {
                'completion': response.get('completion', ''),
                'session_id': response.get('sessionId', ''),
                'trace': response.get('trace', {}),
                'system_usage': response.get('systemUsage', {})
            }
            
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            return {
                'error': str(e),
                'completion': f"Error: {str(e)}"
            }
