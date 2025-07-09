import json
import os
from typing import Any, Tuple

import boto3
from botocore.exceptions import ClientError

from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_import.module_importer import get_instance
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class S3StorageAdapter(StorageProviderPort):
    """
    S3StorageAdapter is a storage provider adapter for handling S3 file operations.

    This class provides methods to read, write, and list files in an S3 bucket.
    It also includes error handling and logging for file operations.
    """

    PREFIX = "s3://"

    SUCCESS_WRITE_FILE = "[S3StorageAdapter] File written successfully at: {file_path}"
    ERROR_WRITE_FILE = "[S3StorageAdapter] Error writing file: {error}"
    ERROR_READ_FILE = "[S3StorageAdapter] Error reading file: {error}"
    FILE_EXIST_ERROR = "[S3StorageAdapter] File already exists at: {file_path}"
    WARNING_FILE_NOT_FOUND = "[S3StorageAdapter] File not found: {file_path}"
    ERROR_LIST_FILE = "[S3StorageAdapter] Error listing files in {bucket_name}: {error}"
    ERROR_LOAD_MODULE = "[S3StorageAdapter] Error loading module: {error}"
    ERROR_EXISTS_FILE = "[S3StorageAdapter] Error checking if file exists: {error}"
    ERROR_EXTRACT_BUCKET_KEY = (
        "[S3StorageAdapter] Error extracting bucket and key: {error}"
    )
    ERROR_DOWNlOAD_FILE = "Error downloading file: {error}"

    def __init__(self):
        self.s3_client = boto3.client("s3")

    @staticmethod
    def supports(path: str) -> bool:
        """
        Check if the S3 storage adapter supports the given path.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: True if the path is supported by the S3 storage adapter, otherwise False.
        """
        return path.startswith(S3StorageAdapter.PREFIX)

    def load_module(
        self, file_path: str, module_type: ModuleTypes, complete_path: str
    ) -> Tuple[Any, str]:
        """
        Load a Python module from the S3 storage and return its instance.

        This method downloads a Python module from an S3 bucket to a local path,
        then attempts to load and return an instance of the module using a specified
        loader function.

        Args:
            file_path (str): The S3 path of the module to be loaded.
            module_type (ModuleTypes): The type of module to load.
            complete_path (str): The complete path used for error reporting.

        Returns:
            Tuple[Any, str]: An instance of the module and the file ID if loaded successfully,
                otherwise raises an exception.

        Raises:
            Exception: If the module cannot be loaded or an error occurs during the process.
        """
        try:
            bucket_name, file_key = self.extract_s3_bucket_and_key(file_path)
            file_id = file_key.split("/")[-1]
            local_dir = os.path.join(
                AppConfig.DEFAULT_TEMP_PATH, module_type.name.lower()
            )

            # Create the directory if it doesn't exist
            os.makedirs(local_dir, exist_ok=True)

            local_path = os.path.join(local_dir, f"{file_id}.py")
            downloaded_path = self.download_file_from_s3(
                bucket_name, f"{file_key}.py", local_path
            )

            instance = get_instance(file_path, downloaded_path)
            if instance is None:
                raise Exception(f"Failed to load module from path {complete_path}")
            return instance, file_id
        except Exception as e:
            logger.error(self.ERROR_LOAD_MODULE.format(error=e))
            raise

    def read_file(self, file_path: str) -> Any:
        """
        Read the content of a file from the S3 storage.

        Args:
            file_path (str): The path of the file to be read.

        Returns:
            Any: The content of the file if read successfully, otherwise None.
        """
        try:
            bucket_name, file_key = self.extract_s3_bucket_and_key(file_path)
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            with response["Body"] as body:
                content = body.read().decode("utf-8")
            return content
        except self.s3_client.exceptions.NoSuchKey:
            logger.warning(self.WARNING_FILE_NOT_FOUND.format(file_path=file_path))
            return None
        except Exception as e:
            logger.error(self.ERROR_READ_FILE.format(error=e))
            return None

    def write_file(self, file_path: str, content: Any) -> bool:
        """
        Write content to a file in the S3 storage.

        Args:
            file_path (str): The path where the file will be stored.
            content (Any): The content to be saved to the file.

        Returns:
            bool: True if the content is saved successfully, otherwise False.
        """
        try:
            if self.exists(file_path):
                raise FileExistsError()
            bucket_name, file_key = self.extract_s3_bucket_and_key(file_path)

            # Convert content to JSON string if it's a dictionary
            if isinstance(content, dict):
                content = json.dumps(content)

            # Ensure content is in bytes
            if isinstance(content, str):
                content = content.encode("utf-8")

            self.s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=content)
            logger.info(self.SUCCESS_WRITE_FILE.format(file_path=file_path))
            return True
        except FileExistsError:
            logger.error(self.FILE_EXIST_ERROR.format(file_path=file_path))
            return False
        except Exception as e:
            logger.error(self.ERROR_WRITE_FILE.format(error=e))
            return False

    def list(self, directory_path: str) -> list[str]:
        """
        List all files in a specified directory in the S3 storage.

        Args:
            directory_path (str): The path to the directory whose files are to be listed.

        Returns:
            list[str]: A list of file names in the specified directory.
        """
        try:
            bucket_name, file_key = self.extract_s3_bucket_and_key(directory_path)
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=file_key
            )
            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"]]
            else:
                return []
        except Exception as e:
            logger.error(
                self.ERROR_LIST_FILE.format(directory_path=directory_path, error=e)
            )
            return []

    def exists(self, file_path: str) -> bool:
        """
        Determine if a file exists in the specified path in the S3 storage.

        This function checks for the existence of a file at the given path
        within the S3 bucket associated with this adapter. It uses the
        `head_object` method to attempt to retrieve metadata for the file.

        Args:
            file_path (str): The path to the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            bucket_name, file_key = self.extract_s3_bucket_and_key(file_path)
            self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            else:
                logger.error(self.ERROR_EXISTS_FILE.format(error=e))
                raise
        except Exception as e:
            logger.error(self.ERROR_EXISTS_FILE.format(error=e))
            raise

    @staticmethod
    def extract_s3_bucket_and_key(file_path: str) -> tuple[str, str]:
        """
        Extract the bucket name and file key from an S3 file path.

        Args:
            file_path (str): The S3 file path, e.g., 's3://s3-bucket-name/file_name.yaml'.

        Returns:
            tuple[str, str]: A tuple containing the bucket name and file key.
        """
        try:
            if not file_path.startswith(S3StorageAdapter.PREFIX):
                raise ValueError(
                    f"The file path does not start with {S3StorageAdapter.PREFIX}"
                )

            # Remove the 's3://' prefix
            path_without_prefix = file_path[5:]

            # Split the remaining path into bucket name and file key
            bucket_name, file_key = path_without_prefix.split("/", 1)

            return bucket_name, file_key
        except Exception as e:
            logger.error(S3StorageAdapter.ERROR_EXTRACT_BUCKET_KEY.format(error=e))
            raise

    def get_creation_datetime(self, file_path: str) -> str:
        """
        Get the last modified time of a file in the S3 storage.

        Args:
            file_path (str): The path of the file to check.

        Returns:
            str: The last modified time of the file as a string, or None if the file does not exist.
        """
        try:
            bucket_name, file_key = self.extract_s3_bucket_and_key(file_path)
            response = self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            last_modified = response["LastModified"]
            return last_modified.timestamp()
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                logger.warning(self.WARNING_FILE_NOT_FOUND.format(file_path=file_path))
                return None
            else:
                logger.error(self.ERROR_EXISTS_FILE.format(error=e))
                raise
        except Exception as e:
            logger.error(self.ERROR_EXISTS_FILE.format(error=e))
            raise

    def download_file_from_s3(
        self, bucket_name: str, file_key, download_path: str
    ) -> str:
        """
        Download a file from an S3 bucket to a local path.

        This method uses the S3 client to download a file specified by the
        bucket name and file key to a local path on the filesystem.

        Args:
            bucket_name (str): The name of the S3 bucket.
            file_key (str): The key (path) of the file in the S3 bucket.
            download_path (str): The local path where the file will be downloaded.

        Returns:
            str: The local path where the file has been downloaded.

        Raises:
            Exception: If there is an error during the download process.
        """
        try:
            self.s3_client.download_file(bucket_name, file_key, download_path)
            return download_path
        except Exception as e:
            logger.error(self.ERROR_DOWNlOAD_FILE.format(error=e))
            raise
