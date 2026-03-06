import boto3
from botocore.config import Config
from app.core.config import settings
import datetime
import logging

logger = logging.getLogger("OneTwenty")

class S3Service:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(S3Service, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance
        
    def _init_client(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    def upload_file(self, content: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        """Uploads file content to S3 and returns the key."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type
            )
            logger.info(f"[S3] Uploaded {key} to {self.bucket_name}")
            return key
        except Exception as e:
            logger.error(f"[S3] Upload failed for {key}: {e}")
            raise e

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generates a pre-signed URL for an S3 key."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"[S3] Failed to generate presigned URL for {key}: {e}")
            raise e
            
s3_service = S3Service()
