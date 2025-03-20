import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from db.models import RawGrantData
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NationalScraper(BaseScraper):
    """Scraper for Italian national government websites"""
    
    def __init__(self, source_name: str, base_url: str):
        super().__init__(source_name, base_url)
        # Determine if we need Selenium based on the source
        self.use_selenium = source_name in ["Gazzetta Ufficiale", "Invitalia", "MISE"]
    
    def get_grant_links(self) -> List[str]:
        """Get links to individual grants based on the national source"""
        # Different approach based on the specific national source
        if "invitalia.it" in self.base_url:
            return self._get_invitalia_links()
        elif "mise.gov.it" in self.base_url:
            return self._get_mise_links()
        elif "gazzettaufficiale.it" in self.base_url:
            return self._get_gazzetta_links()
        elif "simest.it" in self.base_url:
            return self._get_simest_links()
        else:
            return self._get_generic_national_links()
            
    def _get_invitalia_links(self) -> List[str]:
        """Get grant links from Invitalia website"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Invitalia specific selectors
        grant_elements = soup.select(".incentive-card a, .card-incentivi a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
    
    def _get_mise_links(self) -> List[str]:
        """Get grant links from MISE website"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # MISE specific selectors
        grant_elements = soup.select(".incentivi-item a, .agevolazione a, .list-incentivi a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
        
    def _get_gazzetta_links(self) -> List[str]:
        """Get grant links from Gazzetta Ufficiale website"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Gazzetta Ufficiale specific selectors - might need special handling
        # as Gazzetta often has a search interface
        search_url = urljoin(self.base_url, "/ricerca/bandi")
        search_soup = self.get_soup(search_url, use_selenium=True)
        
        grant_elements = search_soup.select(".risultati a, .list-results a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
        
    def _get_simest_links(self) -> List[str]:
        """Get grant links from SIMEST website"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # SIMEST specific selectors
        grant_elements = soup.select(".finanziamenti a, .card-finanziamento a")
        for element in grant_elements:
            if 'href' in element.attrs:
                links.append(self.resolve_url(element['href']))
                
        return links
        
    def _get_generic_national_links(self) -> List[str]:
        """Generic approach for other national sources"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Try various common selectors for national grant links
        selectors = [
            "a[href*='bando']",
            "a[href*='incentiv']",
            "a[href*='agevolazion']",
            "a[href*='contribut']",
            "a[href*='finanziament']",
            ".bandi a",
            ".incentivi a",
            ".agevolazioni a",
            ".finanziamenti a"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if 'href' in element.attrs:
                    # Filter out non-grant links
                    href = element['href']
                    if not any(x in href for x in [
                        'login', 'contatti', 'privacy', 'cookie', 'javascript',
                        'facebook', 'twitter', 'instagram', 'linkedin'
                    ]):
                        links.append(self.resolve_url(href))
        
        # Remove duplicates
        return list(set(links))
    
    def scrape_grant(self, url: str) -> Optional[RawGrantData]:
        """Scrape data for an individual grant from a national website"""
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
        
        # Extract title - try different approaches for national sites
        title_selectors = [
            "h1", "h2.titolo", ".bando-title", ".incentivo-title",
            ".page-title", "header h1", ".title", ".titolo-incentivo",
            ".titolo-bando", ".titolo-agevolazione"
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.text.strip():
                raw_data["title"] = title_elem.text.strip()
                break
        
        # Extract description - national sites often have detailed descriptions
        desc_selectors = [
            ".descrizione", ".description", ".testo", ".content",
            ".descrizione-bando", ".descrizione-incentivo", 
            ".corpo-testo", "article", ".wysiwyg"
        ]
        desc_text = []
        for selector in desc_selectors:
            desc_elems = soup.select(selector)
            for elem in desc_elems:
                desc_text.append(elem.text.strip())
        if desc_text:
            raw_data["description"] = " ".join(desc_text)
        
        # Extract eligibility - national sites often specify eligible businesses
        eligibility_selectors = [
            ".beneficiari", ".destinatari", ".soggetti-ammissibili",
            "div:contains('Beneficiari')", "div:contains('Destinatari')",
            "div:contains('Soggetti ammissibili')", ".a-chi-si-rivolge",
            "div:contains('A chi si rivolge')"
        ]
        for selector in eligibility_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["eligibility"] = elem.text.strip()
                break
        
        # Extract ATECO codes if available - common in Italian national grants
        ateco_selectors = [
            ".codici-ateco", "div:contains('Codici ATECO')",
            "div:contains('ATECO')"
        ]
        for selector in ateco_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                # Try to extract ATECO codes with regex
                ateco_pattern = r'(?:[A-Z]\d{2}(?:\.\d{1,2})?(?:\.\d{1,2})?)'
                matches = re.findall(ateco_pattern, elem.text)
                if matches:
                    raw_data["ateco_code"] = ", ".join(matches)
                else:
                    raw_data["ateco_code"] = elem.text.strip()
                break
        
        # Extract dates
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]+\s+\d{2,4})'
        
        # Opening date
        opening_selectors = [
            ".data-apertura", ".apertura", "div:contains('Apertura')",
            "div:contains('Data di apertura')", "div:contains('Dal')"
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
            ".data-chiusura", ".scadenza", "div:contains('Scadenza')",
            "div:contains('Chiusura')", "div:contains('Termine')",
            "div:contains('Al')", "div:contains('Fino al')"
        ]
        for selector in closing_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["closing_date"] = match.group(0)
                    break
        
        # Extract funding details - important for national incentives
        funding_selectors = [
            ".dotazione", ".budget", ".risorse", ".stanziamento",
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
        
        # Extract max/min request amounts - common in national grants
        limits_selectors = [
            ".contributo", ".importo", ".finanziamento", ".agevolazione",
            "div:contains('Contributo')", "div:contains('Importo')",
            "div:contains('Finanziamento')", "div:contains('Agevolazione')"
        ]
        for selector in limits_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                text = elem.text.lower()
                
                # Try to find max amount
                if "massimo" in text or "max" in text or "fino a" in text:
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
        
        # Extract grant percentage - common in national incentives
        percentage_selectors = [
            ".percentuale", ".intensita", "div:contains('Percentuale')",
            "div:contains('Intensità')", "div:contains('copertura')"
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
        
        # Extract attachments - National sites often provide detailed documentation
        attachment_selectors = [
            "a[href$='.pdf']", "a[href$='.doc']", "a[href$='.docx']",
            "a[href$='.zip']", ".allegati a", ".documenti a",
            ".download a", ".documentazione a", ".modulistica a"
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
                        'compilativo', 'domanda', 'modello', 'template',
                        'dichiarazione', 'schema', 'istanza'
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