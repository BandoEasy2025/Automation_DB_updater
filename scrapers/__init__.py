from scrapers.base_scraper import BaseScraper
from scrapers.regional_scraper import RegionalScraper
from scrapers.chamber_scraper import ChamberScraper

# Import other scrapers when implemented
# from scrapers.national_scraper import NationalScraper
# from scrapers.eu_scraper import EUScraper

def get_scraper(source_name: str, base_url: str, scraper_type: str) -> BaseScraper:
    """
    Factory function to get the appropriate scraper based on type
    
    Args:
        source_name: Name of the source (e.g., "Regione Lombardia")
        base_url: Base URL of the source
        scraper_type: Type of scraper to use
        
    Returns:
        An instance of the appropriate scraper
    """
    if scraper_type == "regional":
        return RegionalScraper(source_name, base_url)
    elif scraper_type == "chamber":
        return ChamberScraper(source_name, base_url)
    elif scraper_type == "national":
        # National scraper not implemented yet, use base scraper
        return BaseScraper(source_name, base_url)
    elif scraper_type == "eu":
        # EU scraper not implemented yet, use base scraper
        return BaseScraper(source_name, base_url)
    else:
        # Default to base scraper
        return BaseScraper(source_name, base_url)