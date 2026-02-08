"""
Supabase client configuration and utilities for the MLB Showdown Bot.

Handles file uploads to Supabase Storage buckets and general Supabase operations.
"""

import os
from pathlib import Path
from typing import Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class SupabaseClientManager:
    """
    Manages Supabase client connections and file operations.
    
    Supports uploading files to Supabase Storage buckets with environment-based
    configuration (staging vs production).
    """
    
    _instances: dict[str, 'SupabaseClientManager'] = {}
    
    def __init__(self):
        """
        Initialize Supabase client manager.
        
        Raises:
            ValueError: If required environment variables are not set.
        """
        self.client = self._create_client()
    
    @staticmethod
    def _create_client() -> Client:
        """
        Create and return a Supabase client for the specified environment.
        
        Returns:
            Initialized Supabase client
            
        Raises:
            ValueError: If required environment variables are missing
        """
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError(
                f"Missing Supabase credentials "
                f"Please set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
        
        return create_client(url, key)
    
    def upload_file(
        self,
        bucket_name: str,
        file_path: str | Path,
        destination_path: str,
        overwrite: bool = False
    ) -> dict:
        """
        Upload a file to a Supabase Storage bucket.
        
        Args:
            bucket_name: Name of the Supabase bucket (e.g., 'card-images')
            file_path: Local file path to upload
            destination_path: Path in the bucket (e.g., 'cards/2025/image.png')
            overwrite: Whether to overwrite if file exists
        
        Returns:
            Dictionary with upload result containing:
                - 'path': The full path in the bucket
                - 'id': The file ID
                - 'success': Boolean indicating success
                - 'error': Error message if failed
        
        Example:
            >>> manager = SupabaseClientManager.get_instance()
            >>> result = manager.upload_file(
            ...     bucket_name='card-images',
            ...     file_path='/local/path/card.png',
            ...     destination_path='cards/2025/player_name.png'
            ... )
            >>> if result['success']:
            ...     print(f"Uploaded to {result['path']}")
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'path': None,
                    'id': None
                }
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Determine file options based on overwrite setting
            file_options = {
                'cacheControl': '3600',
                'upsert': overwrite
            }
            
            response = self.client.storage.from_(bucket_name).upload(
                destination_path,
                file_content,
                file_options
            )
            
            logger.info(f"Successfully uploaded {file_path} to {bucket_name}/{destination_path}")
            
            return {
                'success': True,
                'path': destination_path,
                'error': None
            }
        
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'path': None,
            }
    
    def get_public_url(
        self,
        bucket_name: str,
        file_path: str
    ) -> str:
        """
        Get the public URL for a file in a Supabase bucket.
        
        Args:
            bucket_name: Name of the bucket
            file_path: Path to the file in the bucket
        
        Returns:
            Public URL of the file
            
        Example:
            >>> manager = SupabaseClientManager.get_instance()
            >>> url = manager.get_public_url('card-images', 'cards/2025/player.png')
            >>> print(url)
        """
        try:
            url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            return url
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            return None
    
    def delete_file(
        self,
        bucket_name: str,
        file_path: str
    ) -> dict:
        """
        Delete a file from a Supabase bucket.
        
        Args:
            bucket_name: Name of the bucket
            file_path: Path to the file to delete
        
        Returns:
            Dictionary with deletion result
        """
        try:
            self.client.storage.from_(bucket_name).remove([file_path])
            logger.info(f"Successfully deleted {file_path} from {bucket_name}")
            return {
                'success': True,
                'path': file_path,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return {
                'success': False,
                'path': file_path,
                'error': str(e)
            }
    
    def list_files(
        self,
        bucket_name: str,
        path: str = ''
    ) -> list[dict]:
        """
        List files in a bucket at a given path.
        
        Args:
            bucket_name: Name of the bucket
            path: Path in the bucket to list
        
        Returns:
            List of file metadata dictionaries
        """
        try:
            files = self.client.storage.from_(bucket_name).list(path)
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []


def upload_to_supabase(
    bucket_name: str,
    file_path: str | Path,
    destination_path: str
) -> Optional[str]:
    """
    Upload a file to Supabase in a single call.
    
    Args:
        bucket_name: Name of the bucket
        file_path: Local file path
        destination_path: Destination path in bucket
        env: Environment ('staging' or 'prod')
    
    Returns:
        Public URL of the uploaded file if successful, else None
        
    Example:
        >>> result = upload_to_supabase(
        ...     bucket_name='card-images',
        ...     file_path='/path/to/card.png',
        ...     destination_path='cards/2025/image.png'
        ... )
    """
    manager = SupabaseClientManager()
    upload_data = manager.upload_file(bucket_name, file_path, destination_path)
    return upload_data
