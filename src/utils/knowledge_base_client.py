import os
import json
import boto3
import logging
from typing import Dict, Any, List, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class KnowledgeBaseClient:
    """
    Utility class for interacting with Amazon Bedrock Knowledge Base.
    Handles querying and retrieving information from the knowledge base.
    """
    
    def __init__(self, region_name: str = None):
        """
        Initialize the Knowledge Base client.
        
        Args:
            region_name: AWS region where Knowledge Base is deployed
        """
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize Bedrock Knowledge Base client
        self.kb_client = boto3.client(
            service_name='bedrock-agent-runtime',
            region_name=self.region_name
        )
        
        # Knowledge Base ID from environment variable
        self.knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', '')
        
        logger.info(f"Initialized Knowledge Base client in region {self.region_name}")
    
    def retrieve(self, 
                query: str, 
                max_results: int = 5,
                knowledge_base_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from the Knowledge Base.
        
        Args:
            query: The query text to search for
            max_results: Maximum number of results to return
            knowledge_base_id: Knowledge Base ID to query (override default)
            
        Returns:
            List of relevant documents from the Knowledge Base
        """
        kb_id = knowledge_base_id or self.knowledge_base_id
        
        if not kb_id:
            logger.error("No Knowledge Base ID provided")
            return []
        
        try:
            logger.info(f"Retrieving information from Knowledge Base {kb_id} for query: {query}")
            
            # Call the Retrieve API
            response = self.kb_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            # Extract the retrieved results
            results = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {})
                metadata = {}
                
                # Extract document metadata
                location = content.get('location', {})
                if 's3Location' in location:
                    metadata['source'] = f"s3://{location['s3Location'].get('uri', '')}"
                
                # Get text content
                text_content = ""
                for text_segment in content.get('text', {}).get('segments', []):
                    text_content += text_segment.get('text', '') + "\n"
                
                # Compile result
                results.append({
                    'content': text_content.strip(),
                    'metadata': metadata,
                    'score': result.get('score', 0)
                })
            
            logger.info(f"Retrieved {len(results)} results from Knowledge Base")
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving from Knowledge Base: {str(e)}")
            return []
    
    def sync_knowledge_base(self, data_source_id: str, knowledge_base_id: str = None) -> bool:
        """
        Trigger a sync of the Knowledge Base with its data source.
        
        Args:
            data_source_id: The ID of the data source to sync
            knowledge_base_id: Knowledge Base ID to sync (override default)
            
        Returns:
            Boolean indicating success
        """
        kb_id = knowledge_base_id or self.knowledge_base_id
        
        if not kb_id:
            logger.error("No Knowledge Base ID provided")
            return False
        
        try:
            logger.info(f"Starting sync for Knowledge Base {kb_id} with data source {data_source_id}")
            
            # Use the Bedrock Agent client to start a sync job
            response = boto3.client('bedrock-agent', region_name=self.region_name).start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            
            ingestion_job_id = response.get('ingestionJobId', '')
            logger.info(f"Successfully started sync job with ID: {ingestion_job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error syncing Knowledge Base: {str(e)}")
            return False
    
    def get_sync_status(self, ingestion_job_id: str, knowledge_base_id: str = None) -> Dict[str, Any]:
        """
        Get the status of a Knowledge Base sync job.
        
        Args:
            ingestion_job_id: The ID of the ingestion job
            knowledge_base_id: Knowledge Base ID (override default)
            
        Returns:
            Dictionary with job status details
        """
        kb_id = knowledge_base_id or self.knowledge_base_id
        
        if not kb_id:
            logger.error("No Knowledge Base ID provided")
            return {'status': 'ERROR', 'message': 'No Knowledge Base ID provided'}
        
        try:
            logger.info(f"Getting status for ingestion job {ingestion_job_id}")
            
            # Get the ingestion job status
            response = boto3.client('bedrock-agent', region_name=self.region_name).get_ingestion_job(
                knowledgeBaseId=kb_id,
                ingestionJobId=ingestion_job_id
            )
            
            # Extract status information
            status = response.get('status', 'UNKNOWN')
            statistics = response.get('statistics', {})
            
            logger.info(f"Ingestion job status: {status}")
            return {
                'status': status,
                'statistics': statistics,
                'start_time': response.get('startTime', ''),
                'end_time': response.get('endTime', ''),
                'message': response.get('message', '')
            }
        
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            return {'status': 'ERROR', 'message': str(e)}
