import boto3
import os
from botocore.config import Config

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from us_visa.constants import AWS_SECRET_ACCESS_KEY_ENV_KEY, AWS_ACCESS_KEY_ID_ENV_KEY,REGION_NAME


class S3Client:

    s3_client=None
    s3_resource = None
    def __init__(self, region_name=REGION_NAME):
        """ 
        This Class gets aws credentials from env_variable and creates an connection with s3 bucket 
        and raise exception when environment variable is not set
        """

        if S3Client.s3_resource==None or S3Client.s3_client==None:
            __access_key_id = os.getenv(AWS_ACCESS_KEY_ID_ENV_KEY, )
            __secret_access_key = os.getenv(AWS_SECRET_ACCESS_KEY_ENV_KEY, )
            if __access_key_id is None:
                raise Exception(f"Environment variable: {AWS_ACCESS_KEY_ID_ENV_KEY} is not not set.")
            if __secret_access_key is None:
                raise Exception(f"Environment variable: {AWS_SECRET_ACCESS_KEY_ENV_KEY} is not set.")
        
            # Configure timeouts and retries with higher values for large files
            config = Config(
                region_name=region_name,
                retries={
                    'max_attempts': 5,
                    'mode': 'adaptive'
                },
                read_timeout=900,  # 15 minutes for large model files
                connect_timeout=120,  # 2 minutes
                max_pool_connections=50
            )
            
            S3Client.s3_resource = boto3.resource('s3',
                                            aws_access_key_id=__access_key_id,
                                            aws_secret_access_key=__secret_access_key,
                                            config=config
                                            )
            S3Client.s3_client = boto3.client('s3',
                                        aws_access_key_id=__access_key_id,
                                        aws_secret_access_key=__secret_access_key,
                                        config=config
                                        )
        self.s3_resource = S3Client.s3_resource
        self.s3_client = S3Client.s3_client
        