import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings


def client_storage(region_name="us-east-1"):
    """
    Creates and returns a boto3 client for Minio storage (S3 compatible).
    """
    config = Config(
        retries={"max_attempts": 5, "mode": "standard"},
        signature_version="s3v4",
    )

    client = boto3.client(
        "s3",
        endpoint_url=settings.STORAGE_MEDIA_URL,
        aws_access_key_id=settings.MINIO_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_STORAGE_SECRET_KEY,
        config=config,
        region_name=region_name,
    )
    return client


def upload_file_in_storage(file, file_name):
    """
    Uploads a file to Minio storage.
    """
    try:
        client = client_storage()

        client.upload_fileobj(
            file,
            settings.MINIO_STORAGE_MEDIA_BUCKET_NAME,
            file_name,
        )
        print(f"File {file_name} uploaded successfully.")

    except ClientError as e:
        raise Exception(f"Failed to upload file: {str(e)}")

    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while uploading the file: {str(e)}"
        )
