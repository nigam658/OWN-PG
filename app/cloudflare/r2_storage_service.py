
import boto3
from botocore.config import Config

from app.cloudflare.cloudflare_config import cloudflare_config


class R2StorageService:

    def __init__(self):

        self.bucket_name = cloudflare_config.BUCKET_NAME

        self.client = boto3.client(
            "s3",
            endpoint_url=cloudflare_config.ENDPOINT_URL,
            aws_access_key_id=cloudflare_config.ACCESS_KEY_ID,
            aws_secret_access_key=cloudflare_config.SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path"
                }
            )
        )

    # Check whether R2 bucket is accessible
    def test_connection(self):

        return self.client.head_bucket(
            Bucket=self.bucket_name
        )

    # Upload an image to R2
    def upload_file(
        self,
        file_bytes: bytes,
        file_key: str,
        content_type: str = "image/jpeg"
    ):

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=file_bytes,
            ContentType=content_type
        )

        return file_key

    # Download an image from R2
    def download_file(self, file_key: str) -> bytes:

        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=file_key
        )

        return response["Body"].read()
    
    # Generate a temporary private image URL
    def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 300
    ):

        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": file_key
            },
            ExpiresIn=expiration
        )

    # Delete an image from R2
    def delete_file(self, file_key: str):

        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=file_key
        )

        return True


r2_storage_service = R2StorageService()
