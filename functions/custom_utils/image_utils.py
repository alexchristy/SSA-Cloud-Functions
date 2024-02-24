from typing import Optional
from bs4 import BeautifulSoup # type: ignore
import logging
from .web_utils import get_with_retry


def get_terminal_image_url(url: str) -> Optional[str]:
    """
    Retrieves the image URL from a webpage given its URL.

    Args:
        url (str): The URL of the webpage.

    Returns:
        Optional[str]: The image URL or None if the image could not be found.
    """
    try:
        response = get_with_retry(url)
        if not response:
            logging.info("Failed to get a response from %s", url)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = (
            soup.find("figure", class_="hero banner")
            .find("picture", class_="fixed-aspect")
            .find("img")
        )

        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]
        else:
            logging.info("Image tag with 'src' attribute not found.")
            return None
    except Exception as e:
        logging.error(
            "An error occurred while retrieving the image URL (%s): %s", url, e
        )
        return None