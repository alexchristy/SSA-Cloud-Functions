import logging
import time
from typing import Optional
import requests # type: ignore
from urllib.parse import unquote, quote

def ensure_url_encoded(url: str) -> str:
    """Ensure that the URL is encoded.

    If the URL is not encoded, it will be encoded. If the URL is already encoded,
    it will be returned unchanged.

    Args:
    ----
        url: The URL to encode.

    Returns:
    -------
        The encoded URL.

    """
    unquoted_url = unquote(url)

    if unquoted_url == url:
        return quote(url, safe=":/.-")

    # If the URLs are different, it was already encoded.
    return url

def get_with_retry(url: str) -> Optional[requests.Response]:
    """Send a GET request to the given URL and retry if it fails.

    Args:
    ----
        url: The URL to send the GET request to.

    Returns:
    -------
        The response object if the request was successful, None otherwise.

    """
    logging.debug("Entering get_with_retry() requesting: %s", url)

    max_attempts = 3
    delay = 2
    timeout = 5

    url = ensure_url_encoded(url)

    for attempt in range(max_attempts):
        try:
            logging.debug("Sending GET request.")

            response = requests.get(url, timeout=timeout)

            logging.debug("GET request successful.")
            return response

        except requests.Timeout:
            logging.error("Request to %s timed out.", url)

        except Exception as e:  # Catch any exceptions
            logging.error("Request to %s failed in get_with_retry().", url)
            logging.debug("Error: %s", e)

        # If it was not the last attempt
        if attempt < max_attempts:
            logging.info("Retrying request to %s in %d seconds...", url, delay)
            time.sleep(delay)  # Wait before next attempt
            delay *= 2
            timeout += 5

        # It was the last attempt
        else:
            logging.error("All attempts failed.")

    return None

def save_image_in_cloudfare(api_token: str, account_id: str, cf_img_base_url: str,image_url_to_save: str) -> Optional[str]:
    """Save image to Cloudflare Images.
    
    Args:
    ----
        api_token: The Cloudflare API token.
        account_id: The Cloudflare account ID.
        cf_img_base_url: The Cloudflare Images base URL.
        image_url_to_save: The URL of the image to save.
        
    Returns:
    -------
        The URL of the saved image in Cloudflare Images.
    """
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    data = {
        "url": image_url_to_save,
        "requireSignedURLs": "false"
    }

    api_endpoint_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    logging.info("Sending POST request to %s", api_endpoint_url)

    response = requests.post(api_endpoint_url, headers=headers, files=data)

    if response.status_code != 200:
        logging.error("Failed to save image in Cloudflare Images: %s", response.text)
        return None
    
    image_id = response.json()["result"]["id"]

    return f"{cf_img_base_url}/{image_id}/"