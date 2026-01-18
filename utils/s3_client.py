"""
S3 client utility for uploading user media files to AWS S3.
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import BinaryIO, Optional, Tuple
import logging
from pathlib import Path
import uuid
from datetime import datetime

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3Client:
    """AWS S3 client for handling file uploads."""
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            logger.warning("AWS credentials not configured. S3 uploads will fail.")
            self.s3_client = None
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        
        self.bucket_name = settings.S3_BUCKET_NAME
        self.bucket_url = settings.S3_BUCKET_URL
    
    def generate_s3_key(self, user_id: str, media_type: str, file_extension: str) -> str:
        """
        Generate a unique S3 key for a file.
        
        Args:
            user_id: User UUID
            media_type: Type of media (audio or image)
            file_extension: File extension (e.g., .mp3, .jpg)
        
        Returns:
            S3 object key path
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}{file_extension}"
        
        # Organize files by user and media type
        # e.g., uploads/audio/user-uuid/20250116_143022_a1b2c3d4.mp3
        s3_key = f"uploads/{media_type}/{user_id}/{filename}"
        return s3_key
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to S3.
        
        Args:
            file_obj: File object to upload
            s3_key: S3 object key (path)
            content_type: MIME type of the file
            metadata: Additional metadata to store with the file
        
        Returns:
            Tuple of (success: bool, s3_url: str, error_message: str)
        """
        if not self.s3_client:
            return False, None, "S3 client not configured"
        
        try:
            # Prepare upload arguments
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_obj,
            }
            
            if content_type:
                upload_args['ContentType'] = content_type
            
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Upload the file
            self.s3_client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs={
                    'ContentType': content_type or 'application/octet-stream',
                    'Metadata': metadata or {}
                }
            )
            
            # Generate the public URL
            s3_url = f"{self.bucket_url}/{s3_key}"
            
            logger.info(f"Successfully uploaded file to S3: {s3_key}")
            return True, s3_url, None
            
        except NoCredentialsError:
            error_msg = "AWS credentials not found"
            logger.error(error_msg)
            return False, None, error_msg
            
        except ClientError as e:
            error_msg = f"AWS S3 error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error uploading to S3: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def delete_file(self, s3_key: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
        
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.s3_client:
            return False, "S3 client not configured"
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return True, None
            
        except ClientError as e:
            error_msg = f"AWS S3 error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error deleting from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to a private file.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL or None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not configured")
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None


# Global S3 client instance
s3_client = S3Client()
