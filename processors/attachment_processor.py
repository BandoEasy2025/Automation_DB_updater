import os
import uuid
import mimetypes
import requests
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from db.supabase_client import SupabaseClient
from utils.logger import setup_logger, log_attachment_update

logger = setup_logger(__name__)

class AttachmentProcessor:
    """Process and upload attachments to Supabase buckets"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """
        Initialize the attachment processor
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase_client = supabase_client
        # Initialize mimetypes
        mimetypes.init()
        
    def process_attachments(
        self, 
        bando_id: str, 
        informative_attachments: List[Dict[str, str]], 
        compilative_attachments: List[Dict[str, str]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process and upload all attachments for a grant
        
        Args:
            bando_id: The ID of the grant
            informative_attachments: List of informative attachment data
            compilative_attachments: List of compilative attachment data
            
        Returns:
            Tuple of (processed informative attachments, processed compilative attachments)
        """
        processed_informative = []
        processed_compilative = []
        
        # Process informative attachments
        for idx, attachment in enumerate(informative_attachments):
            result = self._process_single_attachment(
                bando_id, 
                attachment, 
                idx + 1,  # numero (sequence number)
                is_informative=True
            )
            if result:
                processed_informative.append(result)
                
        # Process compilative attachments
        for idx, attachment in enumerate(compilative_attachments):
            result = self._process_single_attachment(
                bando_id, 
                attachment, 
                idx + 1,  # numero (sequence number)
                is_informative=False
            )
            if result:
                processed_compilative.append(result)
                
        return processed_informative, processed_compilative
        
    def _process_single_attachment(
        self, 
        bando_id: str, 
        attachment_data: Dict[str, str], 
        numero: int,
        is_informative: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Process and upload a single attachment
        
        Args:
            bando_id: The ID of the grant
            attachment_data: Dictionary with attachment data
            numero: Sequence number for this attachment
            is_informative: True if informative, False if compilative
            
        Returns:
            Processed attachment data if successful, None otherwise
        """
        url = attachment_data.get("url")
        name = attachment_data.get("name", "")
        
        if not url:
            logger.error(f"Missing URL for attachment: {name}")
            return None
            
        try:
            # Download the file
            logger.info(f"Downloading attachment from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            file_data = response.content
            
            # Extract filename from URL if not provided
            if not name:
                parsed_url = urlparse(url)
                name = os.path.basename(parsed_url.path)
                
            # Sanitize filename
            file_name = self._sanitize_filename(name)
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_name)
            if not mime_type:
                mime_type = "application/octet-stream"  # Default MIME type
                
            # Upload to Supabase bucket
            file_path = self.supabase_client.upload_attachment(
                file_data, 
                file_name, 
                is_informative=is_informative
            )
            
            if not file_path:
                logger.error(f"Failed to upload attachment {file_name}")
                return None
                
            # Insert record in database
            result = self.supabase_client.insert_attachment(
                bando_id=bando_id,
                nome=name,
                file_name=file_name,
                file_path=file_path,
                link_originale=url,
                mime_type=mime_type,
                numero=numero,
                is_informative=is_informative
            )
            
            if result:
                # Log the successful attachment upload
                log_attachment_update(
                    action="uploaded",
                    file_name=file_name,
                    bucket="allegati_informativi" if is_informative else "allegati_compilativi",
                    file_path=file_path
                )
                return result
                
        except Exception as e:
            logger.error(f"Error processing attachment {name} from {url}: {str(e)}")
            
        return None
        
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to ensure it's valid for storage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove potentially dangerous characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Ensure filename isn't too long
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:96] + ext if len(ext) <= 4 else name[:96] + ext[:4]
            
        return filename