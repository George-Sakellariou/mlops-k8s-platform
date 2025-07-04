from minio import Minio
from minio.error import S3Error
import io
import logging
from config import settings

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

class MinIOStorage:
    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MODEL_BUCKET
        self.secure = settings.MINIO_SECURE
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
    
    async def create_bucket_if_not_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise
    
    async def upload_file(self, file_path: str, file_content: bytes) -> str:
        """Upload file to MinIO"""
        try:
            self.client.put_object(
                self.bucket_name,
                file_path,
                io.BytesIO(file_content),
                len(file_content)
            )
            logger.info(f"Uploaded file: {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from MinIO"""
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            data = response.read()
            logger.info(f"Downloaded file: {file_path}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    async def delete_file(self, file_path: str):
        """Delete file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, file_path)
            logger.info(f"Deleted file: {file_path}")
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def list_files(self, prefix: str = ""):
        """List files in bucket"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            file_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(file_list)} files with prefix: {prefix}")
            return file_list
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise