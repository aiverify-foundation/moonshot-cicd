import os
import json
from typing import Any, Tuple, List

from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, AzureError
from urllib.parse import urlparse

from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_import.module_importer import get_instance
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class AzureBlobStorageAdapter(StorageProviderPort):
    """
    AzureBlobStorageAdapter is a storage provider adapter for handling Azure Blob file operations.

    Provides read, write, list, exists, and download functionality for blobs.
    """

    INFIX = ".blob.core.windows.net"

    SUCCESS_WRITE_FILE = "[AzureBlobStorageAdapter] File written successfully at: {file_path}"
    ERROR_WRITE_FILE = "[AzureBlobStorageAdapter] Error writing file: {error}"
    ERROR_READ_FILE = "[AzureBlobStorageAdapter] Error reading file: {error}"
    FILE_EXIST_ERROR = "[AzureBlobStorageAdapter] File already exists at: {file_path}"
    WARNING_FILE_NOT_FOUND = "[AzureBlobStorageAdapter] File not found: {file_path}"
    ERROR_LIST_FILE = "[AzureBlobStorageAdapter] Error listing files in {container_name}: {error}"
    ERROR_LOAD_MODULE = "[AzureBlobStorageAdapter] Error loading module: {error}"
    ERROR_EXISTS_FILE = "[AzureBlobStorageAdapter] Error checking if file exists: {error}"
    ERROR_EXTRACT_CONTAINER_KEY = "[AzureBlobStorageAdapter] Error extracting container and key: {error}"
    ERROR_DOWNLOAD_FILE = "[AzureBlobStorageAdapter] Error downloading file: {error}"

    def __init__(self):
        self.default_credential = DefaultAzureCredential()
        self.account_url = os.getenv("AZURE_BLOB_STORAGE_URL")
        self.blob_service_client = BlobServiceClient(self.account_url, credential=self.default_credential)

    @staticmethod
    def supports(path: str) -> bool:
        """
        Check if the Azure Blob storage adapter supports the given path.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: True if the path is supported by the Azure Blob storage adapter, otherwise False.
        """
        return AzureBlobStorageAdapter.INFIX in path

    def load_module(
        self, file_path: str, module_type: ModuleTypes, complete_path: str
    ) -> Tuple[Any, str]:
        """
        Load a Python module from the Azure Blob Storage and return its instance.

        This method downloads a Python module from a Azure Blob Storage Container to
        a local path, then attempts to load and return an instance of the module
        using a specified loader function.

        Args:
            file_path (str): The Azure Blob Storage path of the module to be loaded.
            module_type (ModuleTypes): The type of module to load.
            complete_path (str): The complete path used for error reporting.

        Returns:
            Tuple[Any, str]: An instance of the module and the file ID if loaded successfully,
                otherwise raises an exception.

        Raises:
            Exception: If the module cannot be loaded or an error occurs during the process.
        """
        try:
            container_name, blob_name = self.extract_container_and_blob(file_path)
            file_id = os.path.basename(blob_name)
            local_dir = os.path.join(AppConfig.DEFAULT_TEMP_PATH, module_type.name.lower())
            os.makedirs(local_dir, exist_ok=True)

            local_path = os.path.join(local_dir, f"{file_id}.py")
            downloaded_path = self.download_file(container_name, f"{blob_name}.py", local_path)
            
            module_name = file_id.replace("-", "_")
            instance = get_instance(module_name, downloaded_path)
            if instance is None:
                raise Exception(f"Failed to load module from path {complete_path}")
            return instance, file_id
        except Exception as e:
            logger.error(self.ERROR_LOAD_MODULE.format(error=e))
            raise

    def read_file(self, file_path: str) -> Any:
        """
        Read the content of a file from the Azure Blob Storage.

        Args:
            file_path (str): The path of the file to be read.

        Returns:
            Any: The content of the file if read successfully, otherwise None.
        """
        try:
            container_name, blob_name = self.extract_container_and_blob(file_path)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            stream = blob_client.download_blob()
            return stream.readall().decode("utf-8")
        except ResourceNotFoundError:
            logger.warning(self.WARNING_FILE_NOT_FOUND.format(file_path=file_path))
            return None
        except Exception as e:
            logger.error(self.ERROR_READ_FILE.format(error=e))
            return None

    def write_file(self, file_path: str, content: Any) -> bool:
        """
        Write content to a file in the Azure Blob Storage.

        Args:
            file_path (str): The path where the file will be stored.
            content (Any): The content to be saved to the file.

        Returns:
            bool: True if the content is saved successfully, otherwise False.
        """
        try:
            if self.exists(file_path):
                raise FileExistsError()

            container_name, blob_name = self.extract_container_and_blob(file_path)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            if isinstance(content, dict):
                content = json.dumps(content)
            if isinstance(content, str):
                content = content.encode("utf-8")

            blob_client.upload_blob(content, overwrite=False)
            logger.info(self.SUCCESS_WRITE_FILE.format(file_path=file_path))
            return True
        except FileExistsError:
            logger.error(self.FILE_EXIST_ERROR.format(file_path=file_path))
            return False
        except Exception as e:
            logger.error(self.ERROR_WRITE_FILE.format(error=e))
            return False

    def list(self, directory_path: str) -> List[str]:
        """
        List all files in a specified directory in the Azure Blob Storage.

        Args:
            directory_path (str): The path to the directory whose files are to be listed.

        Returns:
            list[str]: A list of file names in the specified directory.
        """
        try:
            container_name, INFIX = self.extract_container_and_blob(directory_path)
            container_client = self.blob_service_client.get_container_client(container_name)
            return [blob.name for blob in container_client.list_blobs(name_starts_with=INFIX)]
        except Exception as e:
            logger.error(self.ERROR_LIST_FILE.format(container_name=directory_path, error=e))
            return []

    def exists(self, file_path: str) -> bool:
        """
        Determine if a file exists in the specified path in the Azure Blob Storage.

        This function checks for the existence of a file at the given path within
        the Azure Blob Storage container associated with this adapter. It uses the
        BlobServiceClient to get a blob client and calls `exists()` on it.

        Args:
            file_path (str): The path to the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        Raises:
            AzureError: If there is an error communicating with Azure Blob Storage.
        """
        try:
            container_name, blob_name = self.extract_container_and_blob(file_path)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            return blob_client.exists()
        except AzureError as e:
            logger.error(self.ERROR_EXISTS_FILE.format(error=e))
            raise

    @staticmethod
    def extract_container_and_blob(file_path: str) -> Tuple[str, str]:
        """
        Extract container name and blob name from an Azure Blob Storage URL.

        Args:
            file_path (str): The Azure Blob Storage, eg:
            "https://myaccount.blob.core.windows.net/mycontainer/myfolder/myfile.py"

        Returns:
           tuple[str, str]: A tuple containing the container name and file
        """
        try:
            parsed = urlparse(file_path)
            if AzureBlobStorageAdapter.INFIX not in parsed.netloc:
                raise ValueError(f"Not a valid Azure Blob URL: {file_path}")

            # First segment of path is container
            parts = parsed.path.lstrip("/").split("/", 1)
            if len(parts) < 2:
                raise ValueError(f"URL must contain container and blob path: {file_path}")

            container_name = parts[0]
            blob_name = parts[1]
            return container_name, blob_name
        except Exception as e:
            logger.error(AzureBlobStorageAdapter.ERROR_EXTRACT_CONTAINER_KEY.format(error=e))
            raise

    def get_creation_datetime(self, file_path: str) -> str:
        """
        Get the last modified time of a file in the Azure Blob Storage.

        Args:
            file_path (str): The path of the file to check.

        Returns:
            str: The last modified time of the file as a string, or None if the file does not exist.
        """
        try:
            container_name, blob_name = self.extract_container_and_blob(file_path)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            props = blob_client.get_blob_properties()
            return props.last_modified.timestamp()
        except ResourceNotFoundError:
            logger.warning(self.WARNING_FILE_NOT_FOUND.format(file_path=file_path))
            return None
        except Exception as e:
            logger.error(self.ERROR_EXISTS_FILE.format(error=e))
            raise

    def download_file(self, container_name: str, blob_name: str, download_path: str) -> str:
        """
        Download a file from Azure Blob Storage to a local path.

        This method retrieves a blob from the specified Azure container and saves it
        to the local filesystem at the given path. It uses the Azure BlobServiceClient
        to get a blob client and reads the blob data in binary mode.

        Args:
            container_name (str): The name of the Azure Blob Storage container.
            blob_name (str): The name of the blob (file) within the container.
            download_path (str): The local filesystem path where the file will be saved.

        Returns:
            str: The local path where the file has been downloaded.

        Raises:
            Exception: If there is an error during the download process (e.g., 
                    network issues, file write errors, or blob not found).
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open(download_path, "wb") as f:
                data = blob_client.download_blob().readall()
                f.write(data)
            return download_path
        except Exception as e:
            logger.error(self.ERROR_DOWNLOAD_FILE.format(error=e))
            raise
