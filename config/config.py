import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Database tables
GRANTS_TABLE = "bandi"
INFORMATIVE_ATTACHMENTS_TABLE = "allegati_informativi"
COMPILATIVE_ATTACHMENTS_TABLE = "allegati_compilativi"
STATUS_LOG_TABLE = "bandi_status_log"

# Storage buckets
INFORMATIVE_BUCKET = "allegati-informativi"
COMPILATIVE_BUCKET = "allegati-compilativi"

# Logging configuration
LOG_DIRECTORY = "logs"
GRANT_LOG_FILE = os.path.join(LOG_DIRECTORY, "grant_updates.log")
ATTACHMENT_LOG_FILE = os.path.join(LOG_DIRECTORY, "attachments_updates.log")

# Notification configuration
ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "False").lower() == "true"
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# Status definitions
STATUS_UPCOMING = "In uscita"
STATUS_ACTIVE = "Attivo"
STATUS_CLOSING_SOON = "In scadenza"
STATUS_EXPIRED = "Scaduto"

# Status calculation parameters
CLOSING_SOON_DAYS = 60  # Days before expiry to mark as "closing soon"

# Scraping configuration
SCRAPER_TIMEOUT = 30  # Seconds
SCRAPER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SCRAPER_HEADERS = {
    "User-Agent": SCRAPER_USER_AGENT,
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIRECTORY, exist_ok=True)