from minio import Minio
from minio.error import S3Error
import os
import io

class MinIOStorage:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MODEL_BUCKET", "models")
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False  # Set to True for HTTPS
        )
    
    async def create_bucket_if_not_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
            else:
                print(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
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
            return file_path
        except S3Error as e:
            print(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from MinIO"""
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            return response.read()
        except S3Error as e:
            print(f"Error downloading file: {e}")
            raise
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    async def delete_file(self, file_path: str):
        """Delete file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, file_path)
        except S3Error as e:
            print(f"Error deleting file: {e}")
            raise
    
    def list_files(self, prefix: str = ""):
        """List files in bucket"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            raise