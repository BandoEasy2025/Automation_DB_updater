import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from db.models import RawGrantData
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EUScraper(BaseScraper):
    """Scraper for European Union funding portals"""
    
    def __init__(self, source_name: str, base_url: str):
        super().__init__(source_name, base_url)
        # EU funding portals often require JavaScript and have complex structures
        self.use_selenium = True
        
    def get_grant_links(self) -> List[str]:
        """Get links to individual grants from EU funding portals"""
        # Different approach based on the specific EU portal
        if "ec.europa.eu/info/funding-tenders/opportunities/portal" in self.base_url:
            return self._get_funding_portal_links()
        else:
            return self._get_generic_eu_links()
    
    def _get_funding_portal_links(self) -> List[str]:
        """Get grant links from the main EU Funding & Tenders Portal"""
        # This portal requires Selenium for proper navigation
        browser = self.get_browser()
        links = []
        
        try:
            browser.get(self.base_url)
            # Wait for the page to load
            time.sleep(5)
            
            # Try to find the 'Search Topics' or direct grant links
            search_btn = None
            try:
                # Look for search or topics navigation elements
                search_elements = browser.find_elements_by_xpath("//a[contains(text(), 'Search') or contains(text(), 'Topics')]")
                if search_elements:
                    search_btn = search_elements[0]
            except Exception as e:
                logger.warning(f"Could not find search button: {e}")
            
            # Click on search if found
            if search_btn:
                search_btn.click()
                time.sleep(3)
                
                # Look for filters to get only open calls
                try:
                    status_filter = browser.find_element_by_xpath("//span[contains(text(), 'Status')]")
                    if status_filter:
                        status_filter.click()
                        time.sleep(1)
                        
                        # Select "Open" status
                        open_option = browser.find_element_by_xpath("//li[contains(text(), 'Open')]")
                        if open_option:
                            open_option.click()
                            time.sleep(1)
                            
                            # Apply filter
                            apply_btn = browser.find_element_by_xpath("//button[contains(text(), 'Apply')]")
                            if apply_btn:
                                apply_btn.click()
                                time.sleep(3)
                except Exception as e:
                    logger.warning(f"Could not apply filters: {e}")
            
            # Extract HTML and parse with BeautifulSoup
            html = browser.page_source
            soup = self.get_soup(html)
            
            # Look for grant links using various selectors specific to the EU portal
            selectors = [
                "a.card-topic", 
                "td.title a",
                "div.opportunities-list a", 
                "div.call-for-proposals a",
                "a[href*='topic-details']",
                "a[href*='call-details']"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    if 'href' in element.attrs:
                        href = element['href']
                        # Construct full URL if relative
                        if not href.startswith('http'):
                            href = self.resolve_url(href)
                        links.append(href)
            
            # Remove duplicates
            links = list(set(links))
            
        except Exception as e:
            logger.error(f"Error getting EU Funding Portal links: {e}")
        finally:
            browser.quit()
            
        return links
    
    def _get_generic_eu_links(self) -> List[str]:
        """Generic method to get grant links from other EU sources"""
        soup = self.get_soup(self.base_url, use_selenium=self.use_selenium)
        links = []
        
        # Common patterns for EU funding links
        selectors = [
            "a[href*='funding']",
            "a[href*='grants']",
            "a[href*='tenders']",
            "a[href*='program']",
            "a[href*='call']",
            ".calls a",
            ".funding-opportunities a",
            ".programmes a"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if 'href' in element.attrs:
                    href = element['href']
                    # Filter out non-grant links
                    if not any(x in href for x in [
                        'login', 'user', 'contact', 'privacy', 'cookie', 'javascript',
                        'facebook', 'twitter', 'linkedin', 'youtube'
                    ]):
                        # Construct full URL if relative
                        if not href.startswith('http'):
                            href = self.resolve_url(href)
                        links.append(href)
        
        # Remove duplicates
        return list(set(links))
    
    def scrape_grant(self, url: str) -> Optional[RawGrantData]:
        """Scrape data for an individual grant from an EU funding portal"""
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
        
        # Extract title - EU portals often use these patterns
        title_selectors = [
            "h1", "h1.call-title", ".topic-title", ".call-title",
            ".title-section h2", "div.title", ".headline"
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.text.strip():
                raw_data["title"] = title_elem.text.strip()
                break
        
        # Extract description - EU portals often have detailed descriptions
        desc_selectors = [
            ".description", ".topic-description", ".call-description",
            ".topic-info", ".content-description", "div.content",
            "div.detail"
        ]
        desc_text = []
        for selector in desc_selectors:
            desc_elems = soup.select(selector)
            for elem in desc_elems:
                desc_text.append(elem.text.strip())
        if desc_text:
            raw_data["description"] = " ".join(desc_text)
        
        # Extract eligibility - EU grants often specify eligible countries and entities
        eligibility_selectors = [
            ".eligibility", "div:contains('Eligibility')", "div:contains('Who can apply')",
            ".conditions", "div:contains('Conditions')", "div:contains('Eligible countries')"
        ]
        for selector in eligibility_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["eligibility"] = elem.text.strip()
                break
        
        # Extract dates - EU format is typically DD/MM/YYYY or YYYY-MM-DD
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[a-zA-Z]+\s+\d{2,4})'
        
        # Opening/publication date
        opening_selectors = [
            ".publication-date", "div:contains('Publication date')", 
            "div:contains('Opening date')", "div:contains('Call opens')"
        ]
        for selector in opening_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["opening_date"] = match.group(0)
                    break
        
        # Closing/deadline date
        closing_selectors = [
            ".deadline", "div:contains('Deadline')", "div:contains('Submission deadline')",
            "div:contains('Call closes')", "div:contains('Due date')"
        ]
        for selector in closing_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                match = re.search(date_pattern, elem.text)
                if match:
                    raw_data["closing_date"] = match.group(0)
                    break
        
        # Extract funding details - EU grants often specify budget in EUR
        funding_selectors = [
            ".budget", "div:contains('Budget')", "div:contains('Total budget')",
            ".funding", "div:contains('Funding')"
        ]
        for selector in funding_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                # Try to find currency amount (EU typically uses EUR format)
                money_pattern = r'€\s*[\d.,]+|[\d.,]+\s*€|EUR\s*[\d.,]+|[\d.,]+\s*EUR'
                match = re.search(money_pattern, elem.text)
                if match:
                    raw_data["total_funding"] = match.group(0)
                    break
        
        # Extract topic/sector - EU grants are often categorized by topic or programme
        sector_selectors = [
            ".topic", ".programme", "div:contains('Topic')", 
            "div:contains('Programme')", "div:contains('Action')"
        ]
        for selector in sector_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                raw_data["sector"] = elem.text.strip()
                break
        
        # Extract attachments - EU portals typically provide documentation
        attachment_selectors = [
            "a[href$='.pdf']", "a[href$='.doc']", "a[href$='.docx']",
            "a[href$='.zip']", ".documents a", ".attachments a",
            ".supporting-docs a", ".call-documents a"
        ]
        for selector in attachment_selectors:
            attachments = soup.select(selector)
            for attachment in attachments:
                if 'href' in attachment.attrs:
                    file_url = attachment['href']
                    # Construct full URL if relative
                    if not file_url.startswith('http'):
                        file_url = self.resolve_url(file_url)
                        
                    file_name = attachment.text.strip() or file_url.split('/')[-1]
                    
                    # Determine if informative or compilative
                    # EU often distinguishes between guide documents and forms
                    is_informative = True
                    compilative_keywords = [
                        'form', 'template', 'application form', 'proposal template',
                        'financial', 'budget', 'submission form', 'annex'
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