from pathlib import Path
import logging
from typing import Union

# Import the necessary third-party library
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger("ELESS.HTMLParser")


def parse_html(file_path: Path) -> str:
    """
    Extracts clean, visible text content from an HTML file,
    stripping out tags, scripts, styles, and other noise.

    Args:
        file_path: The Path object pointing to the HTML file.

    Returns:
        A single string containing the cleaned text content,
        or an empty string if extraction fails.
    """
    try:
        # 1. Read the raw HTML content
        # Use 'utf-8' and handle potential decoding errors
        html_content = file_path.read_text(encoding="utf-8", errors="ignore")

        # 2. Parse the HTML using BeautifulSoup
        # The 'lxml' parser is generally faster and more robust than 'html.parser'
        # Ensure 'lxml' is installed if you rely on it: pip install lxml
        soup = BeautifulSoup(html_content, "lxml")

        # 3. Remove unwanted elements (scripts, styles, comments, etc.)
        # Remove all JavaScript and CSS code
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Remove all HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Optional: Remove common navigation/footer elements that are usually noise
        for tag in soup.find_all(["nav", "footer", "header"]):
            tag.decompose()

        # 4. Get the text
        # This extracts all text and joins it with spaces.
        clean_text = soup.get_text(separator=" ", strip=True)

        # 5. Normalize whitespace
        # Replace multiple spaces/newlines with a single space, then join by double newline for paragraphs
        normalized_text = "\n\n".join(
            [p.strip() for p in clean_text.splitlines() if p.strip()]
        )

        logger.debug(f"Successfully extracted text from HTML file {file_path.name}.")
        return normalized_text

    except FileNotFoundError:
        logger.error(f"HTML file not found at: {file_path}")
    except Exception as e:
        # Catch any parsing or I/O errors
        logger.error(
            f"An unexpected error occurred while parsing {file_path.name}: {e}"
        )

    return ""
