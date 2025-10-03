from pathlib import Path
import logging
from typing import Union

# Import the necessary third-party library
from pypdf import PdfReader
from pypdf.errors import PyPdfError  # <-- FIX 1: Corrected exception name to PyPdfError

logger = logging.getLogger("ELESS.PDFParser")


def parse_pdf(file_path: Path) -> str:
    """
    Extracts all text content from a PDF file.

    Args:
        file_path: The Path object pointing to the PDF file.

    Returns:
        A single string containing the concatenated text from all pages,
        or an empty string if extraction fails.
    """

    text_content = []

    try:
        # Create a PdfReader object
        reader = PdfReader(file_path)

        # Check if the PDF is encrypted (pypdf can often handle simple encryption)
        if reader.is_encrypted:
            try:
                # Attempt to decrypt with no password (common for simple protection)
                reader.decrypt("")
            except NotImplementedError:
                # If decryption fails or is not supported
                logger.warning(
                    f"File {file_path.name} is encrypted and could not be read."
                )
                return ""

        # Extract text page by page
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)

        # Join all page text with a clear separator
        return "\n\n---PAGE BREAK---\n\n".join(text_content)

    except FileNotFoundError:
        logger.error(f"PDF file not found at: {file_path}")
    except PyPdfError:  # <-- FIX 2: Catch the corrected exception name
        logger.error(f"File {file_path.name} is not a valid or readable PDF.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing {file_path.name}: {e}"
        )

    return ""
