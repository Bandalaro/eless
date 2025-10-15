import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Union, Generator, List
import logging

# Import performance logging decorator
from ..core.logging_config import log_performance

logger = logging.getLogger("ELESS.FileScanner")


class FileScanner:
    """
    Handles input validation (file or directory) and generates unique
    content hashes for all discovered files.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initializes the scanner, can optionally use file filters from config."""
        self.config = config
        # Define supported extensions (e.g., from a config, or hardcoded for now)
        self.supported_extensions = {
            ".txt",
            ".pdf",
            ".docx",
            ".xlsx",
            ".csv",
            ".html",
            ".md",
            ".bin",
            # Add other extensions as parsers are built
        }

    @log_performance("ELESS.FileScanner")
    def _generate_file_hash(self, file_path: Path) -> str:
        """
        Generates a SHA-256 hash based on the content of the file.
        This hash serves as the unique, content-based identifier (File ID).
        """
        logger.debug(f"Generating hash for file: {file_path.name}")
        hasher = hashlib.sha256()
        block_size = 65536  # 64kb

        try:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    hasher.update(data)
            file_hash = hasher.hexdigest()
            logger.debug(f"Generated hash for {file_path.name}: {file_hash[:12]}...")
            return file_hash
        except OSError as e:
            logger.error(
                f"Error reading file {file_path} for hashing: {e}", exc_info=True
            )
            raise

    @log_performance("ELESS.FileScanner")
    def scan_input(
        self, input_path: Union[str, Path]
    ) -> List[Dict[str, Union[str, Path]]]:
        """
        Takes a path (file or directory) and returns a list of dictionaries for each
        valid, discovered document.

        Returns: List of {'path': Path object, 'hash': SHA-256 string, 'file_id': hash}
        """
        input_path = Path(input_path)
        logger.info(f"Starting scan of input path: {input_path}")

        if not input_path.exists():
            logger.error(f"Input path not found: {input_path}")
            raise FileNotFoundError(f"Input path does not exist: {input_path}")

        files_found = []

        if input_path.is_file():
            # Handle a single file input
            if input_path.suffix.lower() in self.supported_extensions:
                try:
                    file_data = self._process_file(input_path)
                    files_found.append(file_data)
                    logger.info(f"Found 1 supported file: {input_path.name}")
                except Exception as e:
                    logger.error(
                        f"Failed to process file {input_path}: {e}",
                        exc_info=True,
                    )
                    # Add file with error status
                    file_data = {
                        "path": input_path,
                        "hash": "ERROR",
                        "file_id": "ERROR",
                        "extension": input_path.suffix.lower(),
                    }
                    files_found.append(file_data)
            else:
                logger.warning(
                    f"File {input_path.name} skipped: Unsupported extension {input_path.suffix}"
                )

        elif input_path.is_dir():
            # Recursively handle directory input
            logger.info(f"Scanning directory recursively: {input_path}")
            total_files = 0
            skipped_files = 0
            error_files = 0

            for root, _, files in os.walk(input_path):
                root_path = Path(root)
                for file_name in files:
                    total_files += 1
                    file_path = root_path / file_name

                    if file_path.suffix.lower() in self.supported_extensions:
                        try:
                            file_data = self._process_file(file_path)
                            files_found.append(file_data)
                        except Exception as e:
                            logger.error(
                                f"Failed to process file {file_path}: {e}",
                                exc_info=True,
                            )
                            # Add file with error status
                            file_data = {
                                "path": file_path,
                                "hash": "ERROR",
                                "file_id": "ERROR",
                                "extension": file_path.suffix.lower(),
                            }
                            files_found.append(file_data)
                            error_files += 1
                            # Continue to next file on error
                            continue
                    else:
                        logger.debug(
                            f"Skipping file {file_path.name}: Unsupported extension {file_path.suffix}"
                        )
                        skipped_files += 1

            logger.info(
                f"Directory scan complete. Total: {total_files}, Found: {len(files_found)}, Skipped: {skipped_files}, Errors: {error_files}"
            )
        else:
            logger.warning(f"Input is not a file or directory: {input_path}")

        logger.info(f"Scan complete. Found {len(files_found)} processable files")
        return files_found

    @log_performance("ELESS.FileScanner")
    def _process_file(self, file_path: Path) -> Dict[str, Union[str, Path]]:
        """Helper to hash and structure the file data."""
        logger.debug(f"Processing file: {file_path.name}")
        file_hash = self._generate_file_hash(file_path)
        logger.debug(f"Processed file: {file_path.name}, Hash: {file_hash[:12]}...")

        return {
            "path": file_path,
            "hash": file_hash,
            "file_id": file_hash,  # Add for consistency with CLI expectations
            "extension": file_path.suffix.lower(),
        }

    # --- Utility for CLI/Users ---

    def get_supported_extensions(self) -> List[str]:
        """Returns the list of document extensions that ELESS can process."""
        return list(self.supported_extensions)
