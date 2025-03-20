import re
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from db.models import RawGrantData, Grant
from processors.status_calculator import calculate_status
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GrantProcessor:
    """Process raw grant data into structured database format"""
    
    @staticmethod
    def process_raw_grant(raw_grant: RawGrantData) -> Grant:
        """
        Convert raw scraped grant data into a structured Grant object
        
        Args:
            raw_grant: Raw grant data from scraper
            
        Returns:
            Structured Grant object
        """
        # Generate a unique record_id based on the title and URL
        record_id = GrantProcessor._generate_record_id(raw_grant.title, raw_grant.url)
        
        # Create basic grant data
        grant_data = {
            "record_id": record_id,
            "nome_bando": raw_grant.title,
            "promotore": raw_grant.promoter,
            "descrizione_breve": GrantProcessor._extract_short_description(raw_grant.description),
            "descrizione_bando": raw_grant.description,
            "a_chi_si_rivolge": raw_grant.eligibility,
            "settore": raw_grant.sector,
            "codice_ateco": raw_grant.ateco_code,
            "spese_ammissibili": raw_grant.eligible_expenses,
            "link_bando": raw_grant.url,
            "link_sito_bando": raw_grant.website_url or raw_grant.source_url,
            "tipo": raw_grant.type,
            "emanazione": raw_grant.source
        }
        
        # Process dates
        grant_data.update(GrantProcessor._process_dates(raw_grant))
        
        # Process financial info
        grant_data.update(GrantProcessor._process_financial_info(raw_grant))
        
        # Calculate status based on dates
        opening_date = grant_data.get("data_apertura")
        closing_date = grant_data.get("scadenza")
        grant_data["stato"] = calculate_status(opening_date, closing_date)
        
        # Create Grant object
        return Grant(**grant_data)
    
    @staticmethod
    def _generate_record_id(title: str, url: str) -> str:
        """
        Generate a unique record_id based on the title and URL
        
        Args:
            title: Grant title
            url: Grant URL
            
        Returns:
            A unique record_id string
        """
        # Create a unique string based on title and URL
        unique_string = f"{title.lower().strip()}_{url}"
        
        # Generate an MD5 hash (good enough for this purpose)
        hash_obj = hashlib.md5(unique_string.encode())
        return hash_obj.hexdigest()
    
    @staticmethod
    def _extract_short_description(description: Optional[str]) -> Optional[str]:
        """
        Extract a short description from the full description
        
        Args:
            description: Full grant description
            
        Returns:
            Short description (max 200 characters)
        """
        if not description:
            return None
            
        # Take first paragraph or sentence
        first_paragraph = description.split('\n')[0].strip()
        if len(first_paragraph) <= 200:
            return first_paragraph
            
        # If first paragraph is too long, take first sentence
        first_sentence = re.split(r'[.!?]', first_paragraph)[0].strip()
        
        # Truncate if still too long
        if len(first_sentence) > 200:
            return first_sentence[:197] + "..."
            
        return first_sentence
    
    @staticmethod
    def _process_dates(raw_grant: RawGrantData) -> Dict[str, Any]:
        """
        Process date strings into datetime objects
        
        Args:
            raw_grant: Raw grant data
            
        Returns:
            Dictionary with processed date fields
        """
        result = {}
        
        # Process opening date
        if raw_grant.opening_date:
            try:
                parsed_date = GrantProcessor._parse_italian_date(raw_grant.opening_date)
                if parsed_date:
                    result["data_apertura"] = parsed_date
            except Exception as e:
                logger.error(f"Error parsing opening date '{raw_grant.opening_date}': {e}")
        
        # Process closing date
        if raw_grant.closing_date:
            try:
                parsed_date = GrantProcessor._parse_italian_date(raw_grant.closing_date)
                if parsed_date:
                    result["scadenza"] = parsed_date
                    # Set internal deadline 7 days before actual deadline
                    internal_deadline = parsed_date.replace(
                        day=max(1, parsed_date.day - 7)
                    )
                    result["scadenza_interna"] = internal_deadline
            except Exception as e:
                logger.error(f"Error parsing closing date '{raw_grant.closing_date}': {e}")
                
        return result
    
    @staticmethod
    def _parse_italian_date(date_string: str) -> Optional[datetime]:
        """
        Parse Italian date formats into datetime objects
        
        Args:
            date_string: Date string in various Italian formats
            
        Returns:
            datetime object or None if parsing fails
        """
        date_string = date_string.strip()
        
        # Try various Italian date formats
        formats = [
            # DD/MM/YYYY
            r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',
            # DD month YYYY in Italian
            r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
            # YYYY/MM/DD
            r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})'
        ]
        
        for format_pattern in formats:
            match = re.search(format_pattern, date_string, re.IGNORECASE)
            if match:
                if format_pattern == formats[0]:  # DD/MM/YYYY
                    day, month, year = map(int, match.groups())
                    return datetime(year=year, month=month, day=day)
                elif format_pattern == formats[1]:  # DD month YYYY
                    day = int(match.group(1))
                    month_name = match.group(2).lower()
                    year = int(match.group(3))
                    
                    # Convert Italian month names to numbers
                    month_map = {
                        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
                        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
                        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
                    }
                    month = month_map.get(month_name)
                    if month:
                        return datetime(year=year, month=month, day=day)
                elif format_pattern == formats[2]:  # YYYY/MM/DD
                    year, month, day = map(int, match.groups())
                    return datetime(year=year, month=month, day=day)
        
        return None
    
    @staticmethod
    def _process_financial_info(raw_grant: RawGrantData) -> Dict[str, Any]:
        """
        Process financial information from raw grant data
        
        Args:
            raw_grant: Raw grant data
            
        Returns:
            Dictionary with processed financial fields
        """
        result = {}
        
        # Process total funding
        if raw_grant.total_funding:
            try:
                amount = GrantProcessor._extract_amount(raw_grant.total_funding)
                if amount is not None:
                    result["dotazione"] = amount
            except Exception as e:
                logger.error(f"Error parsing total funding '{raw_grant.total_funding}': {e}")
        
        # Process max request
        if raw_grant.max_request:
            try:
                amount = GrantProcessor._extract_amount(raw_grant.max_request)
                if amount is not None:
                    result["richiesta_massima"] = amount
            except Exception as e:
                logger.error(f"Error parsing max request '{raw_grant.max_request}': {e}")
        
        # Process min request
        if raw_grant.min_request:
            try:
                amount = GrantProcessor._extract_amount(raw_grant.min_request)
                if amount is not None:
                    result["richiesta_minima"] = amount
            except Exception as e:
                logger.error(f"Error parsing min request '{raw_grant.min_request}': {e}")
        
        # Process grant percentage
        if raw_grant.grant_percentage:
            try:
                percentage = GrantProcessor._extract_percentage(raw_grant.grant_percentage)
                if percentage is not None:
                    result["percentuale_fondo_perduto"] = percentage
            except Exception as e:
                logger.error(f"Error parsing grant percentage '{raw_grant.grant_percentage}': {e}")
        
        return result
    
    @staticmethod
    def _extract_amount(amount_string: str) -> Optional[float]:
        """
        Extract numerical amount from a string containing currency
        
        Args:
            amount_string: String containing an amount (e.g., "€1.000.000")
            
        Returns:
            Float amount or None if extraction fails
        """
        # Remove currency symbols and separators
        cleaned = amount_string.replace('€', '').replace(' ', '')
        
        # Replace Italian number formatting
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        # Extract the first number found
        match = re.search(r'\d+(?:\.\d+)?', cleaned)
        if match:
            return float(match.group(0))
            
        return None
    
    @staticmethod
    def _extract_percentage(percentage_string: str) -> Optional[float]:
        """
        Extract percentage value from a string
        
        Args:
            percentage_string: String containing a percentage (e.g., "50%")
            
        Returns:
            Float percentage or None if extraction fails
        """
        # Extract the number before the percentage sign
        match = re.search(r'(\d+(?:[,.]\d+)?)\s*%', percentage_string)
        if match:
            # Replace Italian decimal separator
            percentage_val = match.group(1).replace(',', '.')
            return float(percentage_val)
            
        return None