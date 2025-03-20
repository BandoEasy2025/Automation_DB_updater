import time
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from db.models import RawGrantData
from config.config import SCRAPER_HEADERS, SCRAPER_TIMEOUT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseScraper(ABC):
    """Base class for all grant scrapers"""
    
    def __init__(self, source_name: str, base_url: str):
        """
        Initialize the base scraper
        
        Args:
            source_name: Name of the source (e.g., "Regione Lombardia")
            base_url: Base URL of the source
        """
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(SCRAPER_HEADERS)
        # Initialize a headless Chrome browser for JS-heavy sites
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(f"user-agent={SCRAPER_HEADERS['User-Agent']}")
    
    def get_browser(self) -> webdriver.Chrome:
        """Get a configured Chrome browser"""
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=self.chrome_options)
    
    def get_soup(self, url: str, use_selenium: bool = False) -> BeautifulSoup:
        """
        Get BeautifulSoup object from URL
        
        Args:
            url: URL to scrape
            use_selenium: If True, use Selenium for JavaScript-rendered pages
            
        Returns:
            BeautifulSoup object
        """
        if use_selenium:
            browser = self.get_browser()
            try:
                browser.get(url)
                # Wait for JavaScript to load content
                time.sleep(2)
                html = browser.page_source
                return BeautifulSoup(html, 'lxml')
            finally:
                browser.quit()
        else:
            try:
                response = self.session.get(url, timeout=SCRAPER_TIMEOUT)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'lxml')
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {url}: {e}")
                return BeautifulSoup("", 'lxml')  # Return empty soup
    
    def download_file(self, url: str) -> Optional[bytes]:
        """Download a file from URL and return its content as bytes"""
        try:
            response = self.session.get(url, timeout=SCRAPER_TIMEOUT, stream=True)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None
    
    def resolve_url(self, relative_url: str) -> str:
        """Resolve a relative URL against the base URL"""
        return urljoin(self.base_url, relative_url)
    
    @abstractmethod
    def get_grant_links(self) -> List[str]:
        """
        Get list of URLs for individual grants
        
        Returns:
            List of URLs for individual grant pages
        """
        pass
    
    @abstractmethod
    def scrape_grant(self, url: str) -> Optional[RawGrantData]:
        """
        Scrape data for an individual grant
        
        Args:
            url: URL of the grant page
            
        Returns:
            RawGrantData object containing scraped data, or None if scraping fails
        """
        pass
    
    def scrape_all_grants(self) -> List[RawGrantData]:
        """
        Scrape all grants from this source
        
        Returns:
            List of RawGrantData objects
        """
        grants = []
        try:
            grant_links = self.get_grant_links()
            logger.info(f"Found {len(grant_links)} grant links from {self.source_name}")
            
            for link in grant_links:
                try:
                    grant_data = self.scrape_grant(link)
                    if grant_data:
                        grants.append(grant_data)
                except Exception as e:
                    logger.error(f"Error scraping grant at {link}: {e}")
                    continue
                    
            logger.info(f"Successfully scraped {len(grants)} grants from {self.source_name}")
        except Exception as e:
            logger.error(f"Error scraping grants from {self.source_name}: {e}")
            
        return grants