import os
import json
import boto3
import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from botocore.exceptions import ClientError

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class S3Client:
    """
    Utility class for interacting with Amazon S3.
    Handles operations related to storing/retrieving documents, FAQ materials, and booking data.
    """
    
    def __init__(self, region_name: str = None):
        """
        Initialize the S3 client.
        
        Args:
            region_name: AWS region where S3 is deployed
        """
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize S3 client
        self.s3 = boto3.client(
            service_name='s3',
            region_name=self.region_name
        )
        
        # Default buckets from environment variables
        self.faq_bucket = os.environ.get('FAQ_BUCKET', 'travel-assistant-faq')
        self.kb_bucket = os.environ.get('KB_BUCKET', 'travel-assistant-knowledge')
        self.bookings_bucket = os.environ.get('BOOKINGS_BUCKET', 'travel-assistant-bookings')
        
        logger.info(f"Initialized S3 client in region {self.region_name}")
    
    def upload_file(self, file_path: str, bucket: str, object_key: str) -> bool:
        """
        Upload a file to an S3 bucket.
        
        Args:
            file_path: Path to the file to upload
            bucket: S3 bucket name
            object_key: S3 object key
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Uploading file {file_path} to {bucket}/{object_key}")
            self.s3.upload_file(file_path, bucket, object_key)
            logger.info(f"Successfully uploaded file to {bucket}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False
    
    def upload_fileobj(self, file_obj: BinaryIO, bucket: str, object_key: str) -> bool:
        """
        Upload a file-like object to an S3 bucket.
        
        Args:
            file_obj: File-like object to upload
            bucket: S3 bucket name
            object_key: S3 object key
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Uploading file object to {bucket}/{object_key}")
            self.s3.upload_fileobj(file_obj, bucket, object_key)
            logger.info(f"Successfully uploaded file object to {bucket}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file object to S3: {str(e)}")
            return False
    
    def download_file(self, bucket: str, object_key: str, file_path: str) -> bool:
        """
        Download a file from an S3 bucket.
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
            file_path: Path to save the downloaded file
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Downloading file from {bucket}/{object_key} to {file_path}")
            self.s3.download_file(bucket, object_key, file_path)
            logger.info(f"Successfully downloaded file from {bucket}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False
    
    def get_object(self, bucket: str, object_key: str) -> Dict[str, Any]:
        """
        Get an object from an S3 bucket.
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
            
        Returns:
            Dictionary with object data and metadata
        """
        try:
            logger.info(f"Getting object from {bucket}/{object_key}")
            response = self.s3.get_object(Bucket=bucket, Key=object_key)
            
            # Read the object data
            object_data = response['Body'].read().decode('utf-8')
            
            # Get the object metadata
            metadata = {
                'ContentType': response.get('ContentType', ''),
                'ContentLength': response.get('ContentLength', 0),
                'LastModified': response.get('LastModified', ''),
                'Metadata': response.get('Metadata', {})
            }
            
            logger.info(f"Successfully retrieved object from {bucket}/{object_key}")
            return {
                'data': object_data,
                'metadata': metadata
            }
        except ClientError as e:
            logger.error(f"Error getting object from S3: {str(e)}")
            return {
                'data': None,
                'metadata': {},
                'error': str(e)
            }
    
    def list_objects(self, bucket: str, prefix: str = '') -> List[Dict[str, Any]]:
        """
        List objects in an S3 bucket with the given prefix.
        
        Args:
            bucket: S3 bucket name
            prefix: Prefix to filter objects
            
        Returns:
            List of objects with their keys and metadata
        """
        try:
            logger.info(f"Listing objects in {bucket} with prefix '{prefix}'")
            
            # List objects in the bucket
            response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            # Extract object information
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj.get('Key', ''),
                    'size': obj.get('Size', 0),
                    'last_modified': obj.get('LastModified', ''),
                    'etag': obj.get('ETag', '')
                })
            
            logger.info(f"Found {len(objects)} objects in {bucket} with prefix '{prefix}'")
            return objects
        except ClientError as e:
            logger.error(f"Error listing objects in S3: {str(e)}")
            return []
    
    def delete_object(self, bucket: str, object_key: str) -> bool:
        """
        Delete an object from an S3 bucket.
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Deleting object {bucket}/{object_key}")
            self.s3.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Successfully deleted object {bucket}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object from S3: {str(e)}")
            return False
    
    def get_faq_document(self, document_key: str) -> Dict[str, Any]:
        """
        Retrieve an FAQ document from the FAQ bucket.
        
        Args:
            document_key: S3 object key for the FAQ document
            
        Returns:
            Dictionary with document data and metadata
        """
        return self.get_object(self.faq_bucket, document_key)
    
    def list_faq_documents(self, prefix: str = '') -> List[Dict[str, Any]]:
        """
        List FAQ documents in the FAQ bucket.
        
        Args:
            prefix: Prefix to filter documents
            
        Returns:
            List of FAQ documents with their keys and metadata
        """
        return self.list_objects(self.faq_bucket, prefix)
    
    def save_booking_data(self, booking_id: str, booking_data: Dict[str, Any]) -> bool:
        """
        Save booking data to the bookings bucket.
        
        Args:
            booking_id: Booking ID to use as object key
            booking_data: Booking data to save
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Saving booking data for booking {booking_id}")
            
            # Convert booking data to JSON
            booking_json = json.dumps(booking_data)
            
            # Save to S3
            object_key = f"bookings/{booking_id}.json"
            self.s3.put_object(
                Bucket=self.bookings_bucket,
                Key=object_key,
                Body=booking_json,
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved booking data for booking {booking_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving booking data: {str(e)}")
            return False
    
    def get_booking_data(self, booking_id: str) -> Dict[str, Any]:
        """
        Retrieve booking data from the bookings bucket.
        
        Args:
            booking_id: Booking ID to retrieve
            
        Returns:
            Dictionary with booking data
        """
        try:
            logger.info(f"Retrieving booking data for booking {booking_id}")
            
            # Get from S3
            object_key = f"bookings/{booking_id}.json"
            result = self.get_object(self.bookings_bucket, object_key)
            
            if result['data'] is not None:
                booking_data = json.loads(result['data'])
                logger.info(f"Successfully retrieved booking data for booking {booking_id}")
                return booking_data
            else:
                logger.warning(f"No booking data found for booking {booking_id}")
                return {}
        except Exception as e:
            logger.error(f"Error retrieving booking data: {str(e)}")
            return {}
