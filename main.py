import time
import schedule
from datetime import datetime
from typing import List, Dict, Any, Optional

from config.sources import ALL_SOURCES
from config.config import GRANTS_TABLE
from db.supabase_client import SupabaseClient
from db.models import RawGrantData, Grant
from scrapers import get_scraper
from processors.grant_processor import GrantProcessor
from processors.attachment_processor import AttachmentProcessor
from processors.status_calculator import calculate_status
from utils.logger import setup_logger, log_grant_update
from utils.notification import NotificationManager

logger = setup_logger(__name__)

class GrantScraper:
    """Main application for scraping and updating grants"""
    
    def __init__(self):
        """Initialize the grant scraper"""
        self.supabase_client = SupabaseClient()
        self.attachment_processor = AttachmentProcessor(self.supabase_client)
        self.notification_manager = NotificationManager()
        
    def run(self):
        """Run the grant scraper once"""
        logger.info("Starting grant scraper run")
        start_time = time.time()
        
        # Scrape grants from all sources
        for source in ALL_SOURCES:
            try:
                logger.info(f"Scraping grants from {source['name']}")
                
                # Get appropriate scraper for this source
                scraper = get_scraper(
                    source_name=source['name'],
                    base_url=source['url'],
                    scraper_type=source['scraper_type']
                )
                
                # Scrape raw grant data
                raw_grants = scraper.scrape_all_grants()
                logger.info(f"Scraped {len(raw_grants)} grants from {source['name']}")
                
                # Process each grant
                for raw_grant in raw_grants:
                    self._process_grant(raw_grant)
                    
            except Exception as e:
                logger.error(f"Error processing source {source['name']}: {str(e)}")
                continue
                
        # Update status for all grants in the database
        self._update_all_grant_statuses()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed grant scraper run in {elapsed_time:.2f} seconds")
    
    def _process_grant(self, raw_grant: RawGrantData):
        """
        Process a single raw grant
        
        Args:
            raw_grant: Raw grant data from scraper
        """
        try:
            # Process the raw grant data into a structured Grant object
            grant = GrantProcessor.process_raw_grant(raw_grant)
            
            # Check if this grant already exists
            existing_grant = None
            if grant.record_id:
                existing_grant = self.supabase_client.get_grant_by_record_id(grant.record_id)
            
            if not existing_grant:
                # Try to find by name and promoter
                existing_grant = self.supabase_client.get_grant_by_name_and_promoter(
                    grant.nome_bando, 
                    grant.promotore
                )
            
            # Either update existing grant or insert new one
            if existing_grant:
                grant_id = existing_grant['id']
                old_status = existing_grant.get('stato')
                
                # Check which fields need to be updated
                updates = {}
                if grant.scadenza and str(grant.scadenza) != str(existing_grant.get('scadenza')):
                    updates['scadenza'] = grant.scadenza
                if grant.data_apertura and str(grant.data_apertura) != str(existing_grant.get('data_apertura')):
                    updates['data_apertura'] = grant.data_apertura
                if grant.descrizione_bando and grant.descrizione_bando != existing_grant.get('descrizione_bando'):
                    updates['descrizione_bando'] = grant.descrizione_bando
                if grant.dotazione and grant.dotazione != existing_grant.get('dotazione'):
                    updates['dotazione'] = grant.dotazione
                
                # Calculate new status if dates changed
                new_status = calculate_status(grant.data_apertura, grant.scadenza)
                if new_status != old_status:
                    updates['stato'] = new_status
                    
                # Update if there are changes
                if updates:
                    logger.info(f"Updating grant: {grant.nome_bando}")
                    result = self.supabase_client.update_grant(grant_id, updates)
                    
                    # Log status change
                    if 'stato' in updates:
                        log_grant_update(grant.nome_bando, old_status, new_status)
                        self.supabase_client.log_status_change(grant_id, old_status, new_status)
                        
                        # Send notification for status change
                        self.notification_manager.notify_status_change(
                            grant_id=grant_id,
                            grant_name=grant.nome_bando,
                            old_status=old_status,
                            new_status=new_status,
                            grant_url=grant.link_bando
                        )
            else:
                # Insert new grant
                logger.info(f"Inserting new grant: {grant.nome_bando}")
                result = self.supabase_client.insert_grant(grant)
                
                if result:
                    grant_id = result['id']
                    new_status = grant.stato
                    
                    # Log new grant
                    log_grant_update(grant.nome_bando, None, new_status)
                    
                    # Send notification for new grant in important status
                    self.notification_manager.notify_status_change(
                        grant_id=grant_id,
                        grant_name=grant.nome_bando,
                        old_status=None,
                        new_status=new_status,
                        grant_url=grant.link_bando
                    )
                else:
                    logger.error(f"Failed to insert grant: {grant.nome_bando}")
                    return
            
            # Process attachments if available
            if raw_grant.informative_attachments or raw_grant.compilative_attachments:
                grant_id = result['id'] if result else existing_grant['id']
                self.attachment_processor.process_attachments(
                    grant_id,
                    raw_grant.informative_attachments,
                    raw_grant.compilative_attachments
                )
                
        except Exception as e:
            logger.error(f"Error processing grant {raw_grant.title}: {str(e)}")
    
    def _update_all_grant_statuses(self):
        """Update the status of all grants in the database based on current date"""
        logger.info("Updating status for all grants")
        
        # Get all grants from database
        response = self.supabase_client.client.table(GRANTS_TABLE).select("*").execute()
        grants = response.data
        
        if not grants:
            logger.info("No grants found in database")
            return
            
        updated_count = 0
        for grant_data in grants:
            grant_id = grant_data['id']
            old_status = grant_data.get('stato')
            
            # Get dates
            opening_date = grant_data.get('data_apertura')
            closing_date = grant_data.get('scadenza')
            
            if opening_date:
                opening_date = datetime.fromisoformat(opening_date.replace('Z', '+00:00'))
            if closing_date:
                closing_date = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                
            # Calculate new status
            new_status = calculate_status(opening_date, closing_date)
            
            # Update if status changed
            if new_status != old_status:
                logger.info(f"Updating status for grant {grant_data['nome_bando']}: {old_status} -> {new_status}")
                
                # Update in database
                self.supabase_client.update_grant(grant_id, {'stato': new_status})
                
                # Log status change
                log_grant_update(grant_data['nome_bando'], old_status, new_status)
                self.supabase_client.log_status_change(grant_id, old_status, new_status)
                
                # Send notification
                self.notification_manager.notify_status_change(
                    grant_id=grant_id,
                    grant_name=grant_data['nome_bando'],
                    old_status=old_status,
                    new_status=new_status,
                    grant_url=grant_data.get('link_bando')
                )
                
                updated_count += 1
                
        logger.info(f"Updated status for {updated_count} grants")

def run_daily_job():
    """Run the grant scraper as a scheduled daily job"""
    scraper = GrantScraper()
    scraper.run()

def main():
    """Main entry point for the application"""
    logger.info("Starting Grant Scraper and Updater")
    
    # Run immediately on startup
    run_daily_job()
    
    # Schedule to run daily at 2 AM
    schedule.every().day.at("02:00").do(run_daily_job)
    
    logger.info("Scheduled daily run at 02:00")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()