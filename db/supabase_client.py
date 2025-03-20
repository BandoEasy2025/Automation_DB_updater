import os
import io
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

import requests
from supabase import create_client, Client

from config.config import (
    SUPABASE_URL, 
    SUPABASE_KEY,
    GRANTS_TABLE,
    INFORMATIVE_ATTACHMENTS_TABLE,
    COMPILATIVE_ATTACHMENTS_TABLE,
    STATUS_LOG_TABLE,
    INFORMATIVE_BUCKET,
    COMPILATIVE_BUCKET
)
from db.models import Grant, InformativeAttachment, CompilativeAttachment, StatusLog
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SupabaseClient:
    """Client for interacting with Supabase database and storage"""
    
    def __init__(self):
        """Initialize the Supabase client"""
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def get_grant_by_record_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a grant by its record_id"""
        response = self.client.table(GRANTS_TABLE).select("*").eq("record_id", record_id).execute()
        data = response.data
        
        if data and len(data) > 0:
            return data[0]
        return None
    
    def get_grant_by_name_and_promoter(self, name: str, promoter: str) -> Optional[Dict[str, Any]]:
        """Get a grant by its name and promoter"""
        response = self.client.table(GRANTS_TABLE) \
            .select("*") \
            .eq("nome_bando", name) \
            .eq("promotore", promoter) \
            .execute()
        data = response.data
        
        if data and len(data) > 0:
            return data[0]
        return None
    
    def insert_grant(self, grant: Grant) -> Dict[str, Any]:
        """Insert a new grant into the database"""
        grant_dict = grant.to_dict()
        grant_dict["update_in_db"] = datetime.now().isoformat()
        
        response = self.client.table(GRANTS_TABLE).insert(grant_dict).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Inserted new grant: {grant.nome_bando}")
            return response.data[0]
        
        logger.error(f"Failed to insert grant: {grant.nome_bando}")
        return {}
    
    def update_grant(self, grant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing grant in the database"""
        update_data["update_in_db"] = datetime.now().isoformat()
        update_data["updated_at"] = datetime.now().isoformat()
        
        response = self.client.table(GRANTS_TABLE) \
            .update(update_data) \
            .eq("id", grant_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Updated grant with ID: {grant_id}")
            return response.data[0]
        
        logger.error(f"Failed to update grant with ID: {grant_id}")
        return {}
    
    def log_status_change(self, bando_id: str, old_status: str, new_status: str) -> Dict[str, Any]:
        """Log a status change in the status_log table"""
        status_log = StatusLog(
            bando_id=bando_id,
            old_status=old_status,
            new_status=new_status
        )
        
        response = self.client.table(STATUS_LOG_TABLE).insert(status_log.to_dict()).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Logged status change for grant {bando_id}: {old_status} -> {new_status}")
            return response.data[0]
        
        logger.error(f"Failed to log status change for grant {bando_id}")
        return {}
    
    def upload_attachment(
        self, 
        file_data: bytes, 
        file_name: str, 
        is_informative: bool = True
    ) -> Optional[str]:
        """
        Upload an attachment to the appropriate bucket
        
        Args:
            file_data: The file data as bytes
            file_name: The name of the file
            is_informative: True if the attachment is informative, False if compilative
            
        Returns:
            The file path in the bucket if successful, None otherwise
        """
        bucket_name = INFORMATIVE_BUCKET if is_informative else COMPILATIVE_BUCKET
        file_path = f"{uuid.uuid4()}/{file_name}"
        
        try:
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_name)
            if not mime_type:
                mime_type = "application/octet-stream"  # Default MIME type
                
            # Upload file to Supabase Storage
            self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=io.BytesIO(file_data),
                file_options={"content-type": mime_type}
            )
            
            logger.info(f"Uploaded file {file_name} to {bucket_name}/{file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_name} to {bucket_name}: {str(e)}")
            return None
            
    def insert_attachment(
        self, 
        bando_id: str, 
        nome: str, 
        file_name: str, 
        file_path: str, 
        link_originale: Optional[str] = None,
        mime_type: Optional[str] = None,
        numero: Optional[int] = None,
        is_informative: bool = True
    ) -> Dict[str, Any]:
        """
        Insert an attachment record into the database
        
        Args:
            bando_id: The ID of the grant this attachment belongs to
            nome: The name/title of the attachment
            file_name: The file name
            file_path: The path in the Supabase bucket
            link_originale: The original URL of the attachment (optional)
            mime_type: The MIME type of the file (optional)
            numero: The attachment sequence number (optional)
            is_informative: True if the attachment is informative, False if compilative
            
        Returns:
            The inserted attachment record if successful, empty dict otherwise
        """
        table_name = INFORMATIVE_ATTACHMENTS_TABLE if is_informative else COMPILATIVE_ATTACHMENTS_TABLE
        
        if is_informative:
            attachment = InformativeAttachment(
                bando_id=bando_id,
                nome=nome,
                file_name=file_name,
                file_path=file_path,
                link_originale=link_originale,
                mime_type=mime_type,
                numero=numero
            )
        else:
            attachment = CompilativeAttachment(
                bando_id=bando_id,
                nome=nome,
                file_name=file_name,
                file_path=file_path,
                link_originale=link_originale,
                mime_type=mime_type,
                numero=numero
            )
            
        response = self.client.table(table_name).insert(attachment.to_dict()).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Inserted {'informative' if is_informative else 'compilative'} attachment: {nome}")
            return response.data[0]
        
        logger.error(f"Failed to insert {'informative' if is_informative else 'compilative'} attachment: {nome}")
        return {}
    
    def get_grant_attachments(
        self, 
        bando_id: str, 
        is_informative: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all attachments for a grant"""
        table_name = INFORMATIVE_ATTACHMENTS_TABLE if is_informative else COMPILATIVE_ATTACHMENTS_TABLE
        
        response = self.client.table(table_name) \
            .select("*") \
            .eq("bando_id", bando_id) \
            .execute()
            
        return response.data if response.data else []
    
    def download_attachment(
        self, 
        file_path: str, 
        is_informative: bool = True
    ) -> Optional[bytes]:
        """
        Download an attachment from Supabase Storage
        
        Args:
            file_path: The path of the file in the bucket
            is_informative: True if the attachment is informative, False if compilative
            
        Returns:
            The file data as bytes if successful, None otherwise
        """
        bucket_name = INFORMATIVE_BUCKET if is_informative else COMPILATIVE_BUCKET
        
        try:
            response = self.client.storage.from_(bucket_name).download(file_path)
            return response
        except Exception as e:
            logger.error(f"Failed to download file {file_path} from {bucket_name}: {str(e)}")
            return None