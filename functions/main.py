# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn # type: ignore
from firebase_admin import initialize_app # type: ignore
from firebase_functions.params import IntParam, StringParam # type: ignore
from firebase_functions.firestore_fn import ( # type: ignore
  on_document_created,
  Event,
  DocumentSnapshot,
)
import logging
import os
import sentry_sdk
from sentry_sdk.integrations.gcp import GcpIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn="https://661608f63733c2c822bb42df766d439f@o4506224652713984.ingest.sentry.io/4506802305564672",
    integrations=[GcpIntegration(timeout_warning=True)],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

app = initialize_app()

# Can all be found in Cloudflare: Images > Overview
CLOUDFLARE_API_KEY = StringParam("CLOUDFLARE_API_KEY")
CLOUDFLARE_IMGS_ACCOUNT_ID = StringParam("CLOUDFLARE_IMGS_ACCOUNT_ID")
CLOUDFLARE_IMAGE_BASE_URL = StringParam("CLOUDFLARE_IMAGE_BASE_URL")

# Get all environment variables
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_IMGS_ACCOUNT_ID = os.environ.get("CLOUDFLARE_IMGS_ACCOUNT_ID")
CLOUDFLARE_IMAGE_BASE_URL = os.environ.get("CLOUDFLARE_IMAGE_BASE_URL")

# Functions
@on_document_created(document="Terminals/{TerminalName}")
def store_terminal_image(event: Event[DocumentSnapshot]) -> None:
    """Retrieves the terminal's image and stores it in Cloudflare Images. Lastly, it 
    updates the terminal's document with the image URL in Cloudflare Images.
    """
    from custom_utils.image_utils import get_terminal_image_url # type: ignore
    from custom_utils.web_utils import save_image_in_cloudfare # type: ignore

    # Get the terminal image URL from terminal page link
    terminal = event.data.to_dict()

    if not terminal.get("link", None):
        logging.error("Terminal link not found for %s", terminal["name"])
        return
    
    terminal_link = terminal["link"]

    image_url = get_terminal_image_url(terminal_link)

    if not image_url:
        logging.error("Image URL not found for %s", terminal["name"])
        return
    
    # Store the image in Cloudflare Images
    saved_image_url = save_image_in_cloudfare(
        CLOUDFLARE_API_KEY,
        CLOUDFLARE_IMGS_ACCOUNT_ID,
        CLOUDFLARE_IMAGE_BASE_URL,
        image_url
    )

    if not saved_image_url:
        logging.error("Image not saved in Cloudflare Images for %s", terminal["name"])
        return
    
    # Update the terminal document with the image URL in Cloudflare Images
    terminal_ref = event.data.reference

    terminal_ref.update({
        "terminalImageUrl": saved_image_url
    })

    logging.info("Terminal image URL updated for %s", terminal["name"])

    return