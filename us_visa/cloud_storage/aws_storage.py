import boto3
from us_visa.configuration.aws_connection import S3Client
from io import StringIO
from typing import Union,List
import os,sys
import time
from us_visa.logger import logging
from mypy_boto3_s3.service_resource import Bucket
from us_visa.exception import USvisaException
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError
from pandas import DataFrame,read_csv
import pickle


class SimpleStorageService:

    def __init__(self):
        s3_client = S3Client()
        self.s3_resource = s3_client.s3_resource
        self.s3_client = s3_client.s3_client

    def s3_key_path_available(self,bucket_name,s3_key)->bool:
        try:
            bucket = self.get_bucket(bucket_name)
            file_objects = [file_object for file_object in bucket.objects.filter(Prefix=s3_key)]
            if len(file_objects) > 0:
                return True
            else:
                return False
        except Exception as e:
            raise USvisaException(e,sys)
        
        

    @staticmethod
    def read_object(object_name: str, decode: bool = True, make_readable: bool = False, max_retries: int = 3) -> Union[StringIO, str]:
        """
        Method Name :   read_object
        Description :   This method reads the object_name object with kwargs

        Output      :   The column name is renamed
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the read_object method of S3Operations class")

        for attempt in range(max_retries):
            try:
                logging.info(f"Reading object from S3... (attempt {attempt + 1}/{max_retries})")
                func = (
                    lambda: object_name.get()["Body"].read().decode()
                    if decode is True
                    else object_name.get()["Body"].read()
                )
                conv_func = lambda: StringIO(func()) if make_readable is True else func()
                logging.info("Successfully read object from S3")
                logging.info("Exited the read_object method of S3Operations class")
                return conv_func()

            except (ReadTimeoutError, ConnectTimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Timeout error on attempt {attempt + 1}, retrying in {wait_time} seconds: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"All retry attempts failed for reading object from S3: {str(e)}")
                    raise USvisaException(e, sys) from e
            except Exception as e:
                logging.error(f"Error reading object from S3: {str(e)}")
                raise USvisaException(e, sys) from e

    def get_bucket(self, bucket_name: str) -> Bucket:
        """
        Method Name :   get_bucket
        Description :   This method gets the bucket object based on the bucket_name

        Output      :   Bucket object is returned based on the bucket name
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the get_bucket method of S3Operations class")

        try:
            bucket = self.s3_resource.Bucket(bucket_name)
            logging.info("Exited the get_bucket method of S3Operations class")
            return bucket
        except Exception as e:
            raise USvisaException(e, sys) from e

    def get_file_object( self, filename: str, bucket_name: str) -> Union[List[object], object]:
        """
        Method Name :   get_file_object
        Description :   This method gets the file object from bucket_name bucket based on filename

        Output      :   list of objects or object is returned based on filename
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the get_file_object method of S3Operations class")

        try:
            bucket = self.get_bucket(bucket_name)

            file_objects = [file_object for file_object in bucket.objects.filter(Prefix=filename)]

            func = lambda x: x[0] if len(x) == 1 else x

            file_objs = func(file_objects)
            logging.info("Exited the get_file_object method of S3Operations class")

            return file_objs

        except Exception as e:
            raise USvisaException(e, sys) from e

    def load_model(self, model_name: str, bucket_name: str, model_dir: str = None, max_retries: int = 3) -> object:
        """
        Method Name :   load_model
        Description :   This method loads the model_name model from bucket_name bucket with kwargs

        Output      :   list of objects or object is returned based on filename
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the load_model method of S3Operations class")

        for attempt in range(max_retries):
            try:
                func = (
                    lambda: model_name
                    if model_dir is None
                    else model_dir + "/" + model_name
                )
                model_file = func()
                logging.info(f"Loading model from S3: bucket={bucket_name}, key={model_file} (attempt {attempt + 1}/{max_retries})")
                
                file_object = self.get_file_object(model_file, bucket_name)
                logging.info(f"Retrieved file object for model: {model_file}")
                
                model_obj = self.read_object(file_object, decode=False, max_retries=1)  # Single retry for read_object since we're already retrying here
                logging.info(f"Read model object from S3, size: {len(model_obj) if model_obj else 0} bytes")
                
                model = pickle.loads(model_obj)
                logging.info("Successfully loaded and unpickled model from S3")
                logging.info("Exited the load_model method of S3Operations class")
                return model

            except (ReadTimeoutError, ConnectTimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Timeout error on attempt {attempt + 1}, retrying in {wait_time} seconds: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"All retry attempts failed for loading model from S3: bucket={bucket_name}, key={model_file}, error={str(e)}")
                    raise USvisaException(e, sys) from e
            except Exception as e:
                logging.error(f"Error loading model from S3: bucket={bucket_name}, key={model_file}, error={str(e)}")
                raise USvisaException(e, sys) from e

    def create_folder(self, folder_name: str, bucket_name: str) -> None:
        """
        Method Name :   create_folder
        Description :   This method creates a folder_name folder in bucket_name bucket

        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the create_folder method of S3Operations class")

        try:
            self.s3_resource.Object(bucket_name, folder_name).load()

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                folder_obj = folder_name + "/"
                self.s3_client.put_object(Bucket=bucket_name, Key=folder_obj)
            else:
                pass
            logging.info("Exited the create_folder method of S3Operations class")

    def upload_file(self, from_filename: str, to_filename: str,  bucket_name: str,  remove: bool = True):
        """
        Method Name :   upload_file
        Description :   This method uploads the from_filename file to bucket_name bucket with to_filename as bucket filename

        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the upload_file method of S3Operations class")

        try:
            logging.info(
                f"Uploading {from_filename} file to {to_filename} file in {bucket_name} bucket"
            )

            self.s3_resource.meta.client.upload_file(
                from_filename, bucket_name, to_filename
            )

            logging.info(
                f"Uploaded {from_filename} file to {to_filename} file in {bucket_name} bucket"
            )

            if remove is True:
                os.remove(from_filename)

                logging.info(f"Remove is set to {remove}, deleted the file")

            else:
                logging.info(f"Remove is set to {remove}, not deleted the file")

            logging.info("Exited the upload_file method of S3Operations class")

        except Exception as e:
            raise USvisaException(e, sys) from e

    def upload_df_as_csv(self,data_frame: DataFrame,local_filename: str, bucket_filename: str,bucket_name: str,) -> None:
        """
        Method Name :   upload_df_as_csv
        Description :   This method uploads the dataframe to bucket_filename csv file in bucket_name bucket

        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the upload_df_as_csv method of S3Operations class")

        try:
            data_frame.to_csv(local_filename, index=None, header=True)

            self.upload_file(local_filename, bucket_filename, bucket_name)

            logging.info("Exited the upload_df_as_csv method of S3Operations class")

        except Exception as e:
            raise USvisaException(e, sys) from e

    def get_df_from_object(self, object_: object) -> DataFrame:
        """
        Method Name :   get_df_from_object
        Description :   This method gets the dataframe from the object_name object

        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the get_df_from_object method of S3Operations class")

        try:
            content = self.read_object(object_, make_readable=True)
            df = read_csv(content, na_values="na")
            logging.info("Exited the get_df_from_object method of S3Operations class")
            return df
        except Exception as e:
            raise USvisaException(e, sys) from e

    def read_csv(self, filename: str, bucket_name: str) -> DataFrame:
        """
        Method Name :   get_df_from_object
        Description :   This method gets the dataframe from the object_name object

        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        logging.info("Entered the read_csv method of S3Operations class")

        try:
            csv_obj = self.get_file_object(filename, bucket_name)
            df = self.get_df_from_object(csv_obj)
            logging.info("Exited the read_csv method of S3Operations class")
            return df
        except Exception as e:
            raise USvisaException(e, sys) from e