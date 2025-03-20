import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from db.models import RawGrantData
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class RegionalScraper(BaseScraper):
    """Scraper for regional government websites"""
    
    def __init__(self, source_name: str, base_url: str):
        super().__init__(source_name, base_url)
        # Customize based on the specific region
        self.region = source_name
        # Flags to determine which approach to use for different regions
        self.use_selenium = source_name in ["Lombardia", "Lazio", "Veneto"]
        
    def get_grant_links(self) -> List[str]:
        """Get links to individual grants based on the region"""
        # Different regions have different structures
        if self.region == "Lombardia":
            return self._get_lombardia_links()
        elif self.region == "Piemonte":
            return self._get_piemonte_links()
        elif self.region == "Lazio":
            return self._get_lazio_links()
        else:
            return self._get_generic_links()
            
    def _get_lombardia_links(self) -> List[str]:
        """Get grant links from Lombardia region website"""
        soup = self.get_soup(self.base_url, use_selenium=True)
        links = []
        
        # Lombardia specific selectors - adjust based on actual structure
        grant_elements = soup.select(".BandiTable .Risultati a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
    
    def _get_piemonte_links(self) -> List[str]:
        """Get grant links from Piemonte region website"""
        soup = self.get_soup(self.base_url)
        links = []
        
        # Piemonte specific selectors - adjust based on actual structure
        grant_elements = soup.select(".view-bandi .views-row a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
        
    def _get_lazio_links(self) -> List[str]:
        """Get grant links from Lazio region website"""
        soup = self.get_soup(self.base_url, use_selenium=True)
        links = []
        
        # Lazio specific selectors - adjust based on actual structure
        grant_elements = soup.select(".item-bando a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
        
    def _get_generic_links(self) -> List[str]:
        """Generic approach to get grant links"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Try various common selectors for grant links
        selectors = [
            "a[href*='bandi']",
            "a[href*='bando']",
            ".bandi a",
            ".grants a",
            ".contributi a",
            ".finanziamenti a",
            "a:contains('bando')",
            "a:contains('contributo')",
            "a:contains('finanziamento')"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if 'href' in element.attrs:
                    # Filter out links that are likely not grant pages
                    href = element['href']
                    if not any(x in href for x in [
                        'login', 'contatti', 'privacy', 'cookie', 'javascript',
                        'facebook', 'twitter', 'instagram', 'linkedin'
                    ]):
                        links.append(self.resolve_url(href))
        
        # Remove duplicates
        return list(set(links))
    
    def scrape_grant(self, url: str) -> Optional[RawGrantData]:
        """Scrape data for an individual grant from a regional website"""
        soup = self.get_soup(url, use_selenium=self.use_selenium)
        if not soup or not soup.text.strip():
            logger.error(f"Failed to get content from {url}")
            return None
            
        # Initialize raw data
        raw_data = {
            "title": "",
            "promoter": self.region,
            "description": "",
            "url": url,
            "source": self.source_name,
            "source_url": self.base_url,
            "informative_attachments": [],
            "compilative_attachments": []
        }
        
        # Extract title - try different approaches
        title_selectors = [
            "h1", "h2.titolo", ".bando-title", ".titolo-bando",
            ".page-title", "header h1", ".title"
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.text.strip():
                raw_data["title"] = title_elem.text.strip()
                break
        
        # Extract description
        desc_selectors = [
            ".descrizione", ".description", ".bando-description",
            ".testo", ".content", ".field-body", "article p"
        ]
        desc_text = []
        for selector in desc_selectors:
            desc_elems = soup.select(selector)
            for elem in desc_elems:
                desc_text.append(elem.text.strip())
        if desc_text:
            raw_data["description"] = " ".join(desc_text)
        
        # Extract eligibility
        eligibility_selectors = [
            ".destinatari", ".beneficiari", ".a-chi-si-rivolge",
            "div:contains('A chi si rivolge')", "div:contains('Destinatari')"
        ]
        for selector in eligibility_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["eligibility"] = elem.text.strip()
                break
        
        # Extract dates
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]+\s+\d{2,4})'
        opening_selectors = [
            ".data-apertura", ".opening-date", "div:contains('Apertura')",
            "div:contains('Data di apertura')", "div:contains('Inizio')"
        ]
        for selector in opening_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["opening_date"] = match.group(0)
                    break
        
        closing_selectors = [
            ".data-chiusura", ".closing-date", ".scadenza",
            "div:contains('Chiusura')", "div:contains('Scadenza')",
            "div:contains('Data di chiusura')", "div:contains('Termine')"
        ]
        for selector in closing_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["closing_date"] = match.group(0)
                    break
        
        # Extract funding details
        funding_selectors = [
            ".dotazione", ".budget", ".stanziamento",
            "div:contains('Dotazione')", "div:contains('Budget')",
            "div:contains('Finanziamento')"
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
        
        # Extract attachments
        attachment_selectors = [
            "a[href$='.pdf']", "a[href$='.doc']", "a[href$='.docx']",
            "a[href$='.xls']", "a[href$='.xlsx']", ".allegati a",
            ".documenti a", ".download a"
        ]
        for selector in attachment_selectors:
            attachments = soup.select(selector)
            for attachment in attachments:
                if 'href' in attachment.attrs:
                    file_url = self.resolve_url(attachment['href'])
                    file_name = attachment.text.strip() or file_url.split('/')[-1]
                    
                    # Determine if informative or compilative
                    is_informative = True
                    compilative_keywords = [
                        'modulo', 'moduli', 'form', 'formulario', 'compilare',
                        'compilativo', 'domanda', 'application'
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