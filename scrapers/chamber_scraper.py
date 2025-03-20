import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from db.models import RawGrantData
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ChamberScraper(BaseScraper):
    """Scraper for Chamber of Commerce websites"""
    
    def __init__(self, source_name: str, base_url: str):
        super().__init__(source_name, base_url)
        # Chambers of Commerce sites often require JavaScript
        self.use_selenium = True
        
    def get_grant_links(self) -> List[str]:
        """Get links to individual grants from a Chamber of Commerce website"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Common patterns for Chamber of Commerce grant links
        selectors = [
            "a[href*='bandi']",
            "a[href*='contributi']",
            ".contributi a",
            ".bandi a",
            ".finanziamenti a",
            ".incentives a",
            ".list-bandi a",
            ".list-contributi a"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if 'href' in element.attrs:
                    href = element['href']
                    # Filter out non-grant links
                    if not any(x in href for x in [
                        'login', 'contatti', 'privacy', 'cookie', 'javascript',
                        'facebook', 'twitter', 'instagram', 'linkedin'
                    ]):
                        links.append(self.resolve_url(href))
        
        # Remove duplicates
        return list(set(links))
        
    def scrape_grant(self, url: str) -> Optional[RawGrantData]:
        """Scrape data for an individual grant from a Chamber of Commerce website"""
        soup = self.get_soup(url, use_selenium=self.use_selenium)
        if not soup or not soup.text.strip():
            logger.error(f"Failed to get content from {url}")
            return None
            
        # Initialize raw data
        raw_data = {
            "title": "",
            "promoter": self.source_name,
            "description": "",
            "url": url,
            "source": self.source_name,
            "source_url": self.base_url,
            "informative_attachments": [],
            "compilative_attachments": []
        }
        
        # Extract title - Chamber of Commerce sites often use these patterns
        title_selectors = [
            "h1", "h2.titolo", ".titolo-bando", ".bando-title",
            ".page-title", "article h1", ".title", ".heading"
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.text.strip():
                raw_data["title"] = title_elem.text.strip()
                break
        
        # Extract description
        desc_selectors = [
            ".descrizione", ".description", ".testo", ".content",
            ".field-body", "article p", ".bando-content p",
            ".dettaglio-bando p", ".text-content"
        ]
        desc_text = []
        for selector in desc_selectors:
            desc_elems = soup.select(selector)
            for elem in desc_elems:
                desc_text.append(elem.text.strip())
        if desc_text:
            raw_data["description"] = " ".join(desc_text)
        
        # Extract eligibility - Chamber sites often specify eligible businesses
        eligibility_selectors = [
            ".destinatari", ".beneficiari", ".soggetti-ammissibili",
            "div:contains('Beneficiari')", "div:contains('Soggetti ammissibili')",
            "div:contains('Destinatari')", "h3:contains('Chi può partecipare')",
            ".a-chi-si-rivolge", "div:contains('A chi si rivolge')"
        ]
        for selector in eligibility_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["eligibility"] = elem.text.strip()
                break
        
        # Extract sector info - Chambers often categorize by business sector
        sector_selectors = [
            ".settori", ".settore", ".sector",
            "div:contains('Settori')", "div:contains('Settore')"
        ]
        for selector in sector_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["sector"] = elem.text.strip()
                break
        
        # Extract dates
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]+\s+\d{2,4})'
        
        # Opening date
        opening_selectors = [
            ".data-apertura", ".apertura", ".opening-date",
            "div:contains('Apertura')", "div:contains('Data di apertura')",
            "div:contains('Inizio presentazione')"
        ]
        for selector in opening_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["opening_date"] = match.group(0)
                    break
        
        # Closing date
        closing_selectors = [
            ".data-chiusura", ".scadenza", ".termine", ".closing-date",
            "div:contains('Scadenza')", "div:contains('Chiusura')",
            "div:contains('Termine presentazione')", "div:contains('Data di chiusura')"
        ]
        for selector in closing_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["closing_date"] = match.group(0)
                    break
        
        # Extract funding details - Chambers often specify exact amounts
        funding_selectors = [
            ".dotazione", ".budget", ".stanziamento", ".risorse",
            "div:contains('Dotazione')", "div:contains('Budget')",
            "div:contains('Risorse')", "div:contains('Stanziamento')"
        ]
        for selector in funding_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                # Try to find currency amount
                money_pattern = r'€\s*[\d.,]+|[\d.,]+\s*€|\d+[\d.,]*\s*(?:euro|EUR)'
                match = re.search(money_pattern, elem.text)
                if match:
                    raw_data["total_funding"] = match.group(0)
                    break
        
        # Extract grant percentage - Chambers often specify percentage covered
        percentage_selectors = [
            ".percentuale", ".agevolazione",
            "div:contains('Percentuale')", "div:contains('Copertura')",
            "div:contains('Agevolazione')"
        ]
        for selector in percentage_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                # Try to find percentage
                percentage_pattern = r'\d+(?:[,.]\d+)?%'
                match = re.search(percentage_pattern, elem.text)
                if match:
                    raw_data["grant_percentage"] = match.group(0)
                    break
        
        # Extract min/max request amounts
        request_selectors = [
            ".importo", ".contributo", ".sovvenzione",
            "div:contains('Importo')", "div:contains('Contributo')",
            "div:contains('Sovvenzione')"
        ]
        for selector in request_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                text = elem.text.lower()
                
                # Try to find max amount
                if "massimo" in text or "max" in text:
                    money_pattern = r'€\s*[\d.,]+|[\d.,]+\s*€|\d+[\d.,]*\s*(?:euro|EUR)'
                    match = re.search(money_pattern, text)
                    if match:
                        raw_data["max_request"] = match.group(0)
                
                # Try to find min amount
                if "minimo" in text or "min" in text:
                    money_pattern = r'€\s*[\d.,]+|[\d.,]+\s*€|\d+[\d.,]*\s*(?:euro|EUR)'
                    match = re.search(money_pattern, text)
                    if match:
                        raw_data["min_request"] = match.group(0)
        
        # Extract attachments - Chambers often provide detailed documentation
        attachment_selectors = [
            "a[href$='.pdf']", "a[href$='.doc']", "a[href$='.docx']",
            "a[href$='.xls']", "a[href$='.xlsx']", ".allegati a",
            ".documenti a", ".download a", ".documenti-correlati a",
            ".modulistica a"
        ]
        for selector in attachment_selectors:
            attachments = soup.select(selector)
            for attachment in attachments:
                if 'href' in attachment.attrs:
                    file_url = self.resolve_url(attachment['href'])
                    file_name = attachment.text.strip() or file_url.split('/')[-1]
                    
                    # Chambers often clearly mark forms vs informational docs
                    is_informative = True
                    compilative_keywords = [
                        'modulo', 'moduli', 'form', 'formulario', 'compilare',
                        'compilativo', 'domanda', 'application', 'richiesta',
                        'modello', 'istanza', 'dichiarazione'
                    ]
                    for keyword in compilative_keywords:
                        if keyword.lower() in file_name.lower() or keyword.lower() in attachment.text.lower():
                            is_informative = False
                            break
                    
                    attachment_data = {
                        "name": file_name,
                        "url": file_url
                    }
                    
                    if is_informative:
                        raw_data["informative_attachments"].append(attachment_data)
                    else:
                        raw_data["compilative_attachments"].append(attachment_data)
        
        # Create RawGrantData from the dictionary
        try:
            return RawGrantData(**raw_data)
        except Exception as e:
            logger.error(f"Error creating RawGrantData from {url}: {e}")
            return None