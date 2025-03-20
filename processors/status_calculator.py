from datetime import datetime, timedelta
from typing import Optional

from config.config import (
    STATUS_UPCOMING,
    STATUS_ACTIVE,
    STATUS_CLOSING_SOON,
    STATUS_EXPIRED,
    CLOSING_SOON_DAYS
)

def calculate_status(
    opening_date: Optional[datetime] = None,
    closing_date: Optional[datetime] = None
) -> str:
    """
    Calculate the status of a grant based on its opening and closing dates
    
    Args:
        opening_date: The date when the grant opens for applications
        closing_date: The date when the grant closes for applications
        
    Returns:
        Status string: "In uscita", "Attivo", "In scadenza", or "Scaduto"
    """
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # If no dates provided, default to active
    if not opening_date and not closing_date:
        return STATUS_ACTIVE
    
    # If only closing date is provided
    if closing_date and not opening_date:
        if current_date > closing_date:
            return STATUS_EXPIRED
        elif current_date > (closing_date - timedelta(days=CLOSING_SOON_DAYS)):
            return STATUS_CLOSING_SOON
        else:
            return STATUS_ACTIVE
    
    # If only opening date is provided
    if opening_date and not closing_date:
        if current_date < opening_date:
            return STATUS_UPCOMING
        else:
            return STATUS_ACTIVE
    
    # If both dates are provided
    if opening_date and closing_date:
        if current_date < opening_date:
            return STATUS_UPCOMING
        elif current_date > closing_date:
            return STATUS_EXPIRED
        elif current_date > (closing_date - timedelta(days=CLOSING_SOON_DAYS)):
            return STATUS_CLOSING_SOON
        else:
            return STATUS_ACTIVE
    
    # Default fallback
    return STATUS_ACTIVE