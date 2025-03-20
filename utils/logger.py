import os
import logging
from datetime import datetime
from typing import Optional

from config.config import LOG_DIRECTORY, GRANT_LOG_FILE, ATTACHMENT_LOG_FILE

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger for a specific module
    
    Args:
        name: The name of the logger (usually __name__)
        log_file: Optional log file path (if None, logs to console only)
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    if logger.handlers:  # Return logger if already configured
        return logger
        
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s]: %(message)s')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def log_grant_update(grant_name: str, old_status: Optional[str], new_status: str) -> None:
    """
    Log a grant status update to the dedicated log file
    
    Args:
        grant_name: Name of the grant
        old_status: Previous status (or None if new grant)
        new_status: New status
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if old_status:
        message = f"[{timestamp}] Grant '{grant_name}' changed from '{old_status}' to '{new_status}'."
    else:
        message = f"[{timestamp}] New grant '{grant_name}' created with status '{new_status}'."
    
    # Ensure the log directory exists
    os.makedirs(os.path.dirname(GRANT_LOG_FILE), exist_ok=True)
    
    # Append to log file
    with open(GRANT_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def log_attachment_update(
    action: str, 
    file_name: str, 
    bucket: str, 
    file_path: str
) -> None:
    """
    Log an attachment update to the dedicated log file
    
    Args:
        action: The action performed (e.g., "uploaded", "updated", "deleted")
        file_name: The name of the file
        bucket: The bucket name
        file_path: The file path in the bucket
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"[{timestamp}] {action.capitalize()} file '{file_name}' to '{bucket}' bucket, file path: {file_path}."
    
    # Ensure the log directory exists
    os.makedirs(os.path.dirname(ATTACHMENT_LOG_FILE), exist_ok=True)
    
    # Append to log file
    with open(ATTACHMENT_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')