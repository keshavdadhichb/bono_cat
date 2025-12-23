"""
Google Drive Integration for File Monitoring and Uploads.

This module provides functionality to watch for new files in Google Drive,
download input images, and upload generated outputs.
"""

import os
import io
import time
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import structlog

logger = structlog.get_logger()


@dataclass
class DriveFile:
    """Represents a file in Google Drive."""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None


class GoogleDriveClient:
    """
    Google Drive API client for file operations.
    
    Handles authentication, folder watching, file downloads, and uploads.
    
    Example:
        client = GoogleDriveClient("./credentials.json")
        client.authenticate()
        files = client.list_files(folder_id)
        client.download_file(file_id, "./local_path.png")
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    def __init__(
        self,
        credentials_path: str,
        token_path: str = "token.json"
    ):
        """
        Initialize the Google Drive client.
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON
            token_path: Path to store/load access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds: Optional[Credentials] = None
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API.
        
        Will trigger OAuth flow if no valid token exists.
        
        Returns:
            bool: True if authentication successful
        """
        # Load existing token
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(
                self.token_path, self.SCOPES
            )
        
        # Refresh or create new token
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save token for next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        # Build service
        self.service = build('drive', 'v3', credentials=self.creds)
        logger.info("Google Drive authentication successful")
        return True
    
    def list_files(
        self,
        folder_id: str,
        mime_types: Optional[List[str]] = None,
        page_size: int = 100
    ) -> List[DriveFile]:
        """
        List files in a folder.
        
        Args:
            folder_id: Google Drive folder ID
            mime_types: Optional list of MIME types to filter
            page_size: Maximum number of files to return
            
        Returns:
            list: List of DriveFile objects
        """
        query = f"'{folder_id}' in parents and trashed = false"
        
        if mime_types:
            mime_queries = [f"mimeType = '{mt}'" for mt in mime_types]
            query += f" and ({' or '.join(mime_queries)})"
        
        results = self.service.files().list(
            q=query,
            pageSize=page_size,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
        ).execute()
        
        files = []
        for item in results.get('files', []):
            files.append(DriveFile(
                id=item['id'],
                name=item['name'],
                mime_type=item['mimeType'],
                size=item.get('size'),
                created_time=item.get('createdTime'),
                modified_time=item.get('modifiedTime')
            ))
        
        return files
    
    def list_image_files(self, folder_id: str) -> List[DriveFile]:
        """List image files in a folder."""
        return self.list_files(
            folder_id,
            mime_types=[
                'image/png',
                'image/jpeg',
                'image/jpg',
                'image/webp'
            ]
        )
    
    def download_file(self, file_id: str, destination: str) -> str:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            destination: Local path to save the file
            
        Returns:
            str: Path to downloaded file
        """
        request = self.service.files().get_media(fileId=file_id)
        
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        with open(destination, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(
                        "Download progress",
                        progress=f"{int(status.progress() * 100)}%"
                    )
        
        logger.info("File downloaded", file_id=file_id, destination=destination)
        return destination
    
    def upload_file(
        self,
        file_path: str,
        folder_id: str,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local path to the file
            folder_id: Destination folder ID
            file_name: Optional custom name (defaults to local filename)
            mime_type: Optional MIME type (auto-detected if not provided)
            
        Returns:
            str: Uploaded file ID
        """
        if file_name is None:
            file_name = Path(file_path).name
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        logger.info("File uploaded", file_id=file_id, name=file_name)
        return file_id
    
    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> str:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the new folder
            parent_folder_id: Optional parent folder ID
            
        Returns:
            str: Created folder ID
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        logger.info("Folder created", folder_id=folder_id, name=folder_name)
        return folder_id
    
    def watch_folder(
        self,
        folder_id: str,
        callback: Callable[[List[DriveFile]], None],
        poll_interval: int = 30,
        stop_event: Optional[Any] = None
    ):
        """
        Watch a folder for new files (polling-based).
        
        Args:
            folder_id: Folder to watch
            callback: Function to call when new files are found
            poll_interval: Seconds between polls
            stop_event: Optional threading.Event to stop watching
        """
        known_files = set()
        
        # Initial scan
        initial_files = self.list_image_files(folder_id)
        for f in initial_files:
            known_files.add(f.id)
        
        logger.info(
            "Started watching folder",
            folder_id=folder_id,
            initial_files=len(known_files)
        )
        
        while True:
            if stop_event and stop_event.is_set():
                break
            
            time.sleep(poll_interval)
            
            try:
                current_files = self.list_image_files(folder_id)
                new_files = [f for f in current_files if f.id not in known_files]
                
                if new_files:
                    logger.info("New files detected", count=len(new_files))
                    callback(new_files)
                    for f in new_files:
                        known_files.add(f.id)
                        
            except Exception as e:
                logger.error("Error watching folder", error=str(e))
    
    def download_batch(
        self,
        files: List[DriveFile],
        destination_dir: str
    ) -> List[str]:
        """
        Download multiple files to a directory.
        
        Args:
            files: List of DriveFile objects to download
            destination_dir: Local directory to save files
            
        Returns:
            list: Paths to downloaded files
        """
        Path(destination_dir).mkdir(parents=True, exist_ok=True)
        
        downloaded = []
        for file in files:
            dest_path = Path(destination_dir) / file.name
            self.download_file(file.id, str(dest_path))
            downloaded.append(str(dest_path))
        
        return downloaded
    
    def upload_batch(
        self,
        file_paths: List[str],
        folder_id: str
    ) -> List[str]:
        """
        Upload multiple files to a folder.
        
        Args:
            file_paths: List of local file paths
            folder_id: Destination folder ID
            
        Returns:
            list: List of uploaded file IDs
        """
        uploaded_ids = []
        for path in file_paths:
            file_id = self.upload_file(path, folder_id)
            uploaded_ids.append(file_id)
        
        return uploaded_ids
