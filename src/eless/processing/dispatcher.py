import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Generator

# Import core components and necessary placeholders (to be created next)
from ..core.state_manager import StateManager, FileStatus
from ..core.archiver import Archiver
from ..core.logging_config import log_performance

# Import parser functions (these files/functions will be created in the subsequent steps)
from .parsers.text_chunker import chunk_text
from .streaming_processor import StreamingDocumentProcessor, BatchProcessor

# Initialize logger early
logger = logging.getLogger("ELESS.Dispatcher")

# Import parsers with fallback for missing dependencies
try:
    from .parsers import pdf_parser

    PDF_AVAILABLE = True
except ImportError:
    logger.warning("PDF parser not available - install pypdf")
    PDF_AVAILABLE = False

try:
    from .parsers import office_parser

    OFFICE_AVAILABLE = True
except ImportError:
    logger.warning("Office parser not available - install python-docx and openpyxl")
    OFFICE_AVAILABLE = False

try:
    from .parsers import table_parser

    TABLE_AVAILABLE = True
except ImportError:
    logger.warning("Table parser not available - install pandas and openpyxl")
    TABLE_AVAILABLE = False

try:
    from .parsers import html_parser

    HTML_AVAILABLE = True
except ImportError:
    logger.warning("HTML parser not available - install beautifulsoup4 and lxml")
    HTML_AVAILABLE = False


class Dispatcher:
    """
    Manages the processing workflow for individual documents.
    It orchestrates scanning, state checking, parsing, and chunking.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        state_manager: StateManager,
        archiver: Archiver,
        resource_monitor=None,
    ):
        self.config = config
        self.state_manager = state_manager
        self.archiver = archiver
        self.resource_monitor = resource_monitor

        # Initialize streaming processor for memory-efficient processing
        self.streaming_processor = StreamingDocumentProcessor(config)

        # Initialize batch processor if resource monitor is available
        if resource_monitor:
            self.batch_processor = BatchProcessor(config, resource_monitor)
        else:
            self.batch_processor = None

        # Mapping file extensions to their respective parser functions
        self.parser_map = {
            ".txt": self._handle_text_file,
            ".md": self._handle_text_file,
            ".bin": self._handle_binary_file,
        }

        # Add parsers conditionally based on availability
        if PDF_AVAILABLE:
            self.parser_map[".pdf"] = pdf_parser.parse_pdf
        if OFFICE_AVAILABLE:
            self.parser_map[".docx"] = office_parser.parse_docx
        if TABLE_AVAILABLE:
            self.parser_map[".xlsx"] = table_parser.parse_xlsx
            self.parser_map[".csv"] = table_parser.parse_csv
        if HTML_AVAILABLE:
            self.parser_map[".html"] = html_parser.parse_html

        logger.info(
            f"Dispatcher initialized with parsers for: {list(self.parser_map.keys())}"
        )

    def _get_raw_text(self, file_path: Path, extension: str) -> str:
        """
        Routes the file path to the correct parser function to extract raw text.
        """
        parser_func = self.parser_map.get(extension)

        if parser_func:
            logger.debug(f"Dispatching {file_path.name} to {parser_func.__name__}...")
            return parser_func(file_path)
        else:
            # Should be caught by FileScanner, but acts as a final safety check
            logger.error(f"No parser found for extension: {extension}")
            return ""

    def _handle_text_file(self, file_path: Path) -> str:
        """Simple handler for raw text and markdown files."""
        try:
            # Check if file can be processed and if streaming is needed
            if not self.streaming_processor.can_process_file(file_path):
                logger.error(f"File {file_path.name} is too large to process")
                return ""

            # Use 'utf-8' and handle potential decoding errors gracefully
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error reading text file {file_path.name}: {e}")
            return ""

    def _handle_binary_file(self, file_path: Path) -> str:
        """Handler for binary files - always return empty to trigger error."""
        return ""

    def process_document(
        self, file_data: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Main function to process a single document from start (parsing)
        to finish (yielding chunks).

        This implements the "skip/resume" logic based on the StateManager.
        Yields: Chunks ready for embedding.
        """
        file_path: Path = file_data["path"]
        file_hash: str = file_data["hash"]
        extension: str = file_data["extension"]

        # Check file size against limits
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        max_file_size_mb = self.config.get("resource_limits", {}).get(
            "max_file_size_mb", 100
        )
        if file_size_mb > max_file_size_mb:
            logger.warning(
                f"File {file_path} size {file_size_mb:.2f}MB exceeds limit of {max_file_size_mb}MB, processing anyway"
            )

        if file_hash == "ERROR":
            # File that failed scanning
            logger.error(f"Failed to scan file {file_path.name}")
            self.state_manager.add_or_update_file(
                "ERROR",
                FileStatus.ERROR,
                file_path=str(file_path),
                metadata={"error": "Failed to scan file"},
            )
            return

        current_status = self.state_manager.get_status(file_hash)

        if current_status == FileStatus.LOADED:
            logger.info(f"File {file_hash[:8]} is already LOADED. Skipping.")
            return

        # -------------------------------------------------------------
        # STAGE 1: Checkpoint (Chunking/Parsing)
        # -------------------------------------------------------------
        raw_text_chunks = None

        if current_status in [FileStatus.CHUNKED, FileStatus.EMBEDDED]:
            # RESUME PATH: Load chunks from cache if they exist
            raw_text_chunks = self.archiver.load_chunks(file_hash)
            if raw_text_chunks is not None:
                logger.info(f"Resuming {file_hash[:8]}. Loaded chunks from cache.")

        if raw_text_chunks is None:
            # RUN PATH: Extract text and chunk it
            self.state_manager.add_or_update_file(
                file_hash, FileStatus.SCANNED, file_path=str(file_path)
            )
            logger.info(f"Processing new file: {file_path.name}...")

            # Check if we should use streaming processing
            if self.streaming_processor.should_use_streaming(
                file_path
            ) and extension in [".txt", ".md"]:
                logger.info(
                    f"Using streaming processing for large file: {file_path.name}"
                )

                try:
                    # Process file using streaming
                    raw_text_chunks = list(
                        self.streaming_processor.process_large_text_file(
                            file_path=file_path,
                            file_hash=file_hash,
                            chunker_func=chunk_text,
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Error during streaming processing of {file_path.name}: {e}"
                    )
                    self.state_manager.add_or_update_file(
                        file_hash,
                        FileStatus.ERROR,
                        file_path=str(file_path),
                        metadata={"error": str(e)},
                    )
                    return

            else:
                # Traditional processing for smaller files or non-text files
                try:
                    raw_text = self._get_raw_text(file_path, extension)
                    if not raw_text:
                        logger.error(f"Failed to extract text from {file_path.name}")
                        self.state_manager.add_or_update_file(
                            file_hash,
                            FileStatus.ERROR,
                            file_path=str(file_path),
                            metadata={"error": "Failed to extract text."},
                        )
                        return

                    # Use the chunker (which will be defined next)
                    chunk_config = self.config["chunking"]
                    raw_text_chunks = chunk_text(
                        raw_text=raw_text,
                        file_hash=file_hash,
                        chunk_size=chunk_config["chunk_size"],
                        chunk_overlap=chunk_config["chunk_overlap"],
                    )
                except Exception as e:
                    logger.error(f"Error during processing of {file_path.name}: {e}")
                    self.state_manager.add_or_update_file(
                        file_hash,
                        FileStatus.ERROR,
                        file_path=str(file_path),
                        metadata={"error": str(e)},
                    )
                    return

            if not raw_text_chunks:
                self.state_manager.add_or_update_file(
                    file_hash,
                    FileStatus.ERROR,
                    file_path=str(file_path),
                    metadata={"error": "No chunks created."},
                )
                return

            if not raw_text_chunks:
                self.state_manager.add_or_update_file(
                    file_hash,
                    FileStatus.ERROR,
                    file_path=str(file_path),
                    metadata={"error": "No chunks created."},
                )
                return

            else:
                # Traditional processing for smaller files or non-text files
                try:
                    raw_text = self._get_raw_text(file_path, extension)
                    if not raw_text:
                        logger.error(f"Failed to extract text from {file_path.name}")
                        self.state_manager.add_or_update_file(
                            file_hash,
                            FileStatus.ERROR,
                            file_path=str(file_path),
                            metadata={"error": "Failed to extract text."},
                        )
                        return

                    # Use the chunker (which will be defined next)
                    chunk_config = self.config["chunking"]
                    raw_text_chunks = chunk_text(
                        raw_text=raw_text,
                        file_hash=file_hash,
                        chunk_size=chunk_config["chunk_size"],
                        chunk_overlap=chunk_config["chunk_overlap"],
                    )
                except Exception as e:
                    logger.error(f"Error during processing of {file_path.name}: {e}")
                    self.state_manager.add_or_update_file(
                        file_hash,
                        FileStatus.ERROR,
                        file_path=str(file_path),
                        metadata={"error": str(e)},
                    )
                    return

            if not raw_text_chunks:
                self.state_manager.add_or_update_file(
                    file_hash,
                    FileStatus.ERROR,
                    file_path=str(file_path),
                    metadata={"error": "No chunks created."},
                )
                return

            # Save chunks and update status
            self.archiver.save_chunks(file_hash, raw_text_chunks)
            self.state_manager.add_or_update_file(
                file_hash, FileStatus.CHUNKED, file_path=str(file_path)
            )
            logger.info(
                f"File {file_hash[:8]} chunked ({len(raw_text_chunks)} chunks) and saved to cache."
            )

        # -------------------------------------------------------------
        # STAGE 2: Yield Chunks for Embedding (External Step)
        # -------------------------------------------------------------
        for chunk in raw_text_chunks:
            yield chunk

    @log_performance("ELESS.Dispatcher")
    def parse_and_chunk(
        self, file_path: Path, file_meta: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse and chunk a single file. This is the method called by the CLI.

        Args:
            file_path: Path to the file to process
            file_meta: Metadata dictionary containing file information

        Returns:
            List of text chunks ready for embedding
        """
        logger.info(f"Starting parse and chunk for file: {file_path.name}")

        try:
            # Extract basic info from file_meta
            file_hash = file_meta.get("file_id") or file_meta.get("hash")
            extension = file_meta.get("extension", file_path.suffix.lower())

            # Check if we should use streaming processing
            if self.streaming_processor.should_use_streaming(
                file_path
            ) and extension in [".txt", ".md"]:
                logger.info(
                    f"Using streaming processing for large file: {file_path.name}"
                )

                # Process file using streaming
                chunks = list(
                    self.streaming_processor.process_large_text_file(
                        file_path=file_path,
                        file_hash=file_hash,
                        chunker_func=chunk_text,
                    )
                )
                logger.info(
                    f"Created {len(chunks)} chunks using streaming from {file_path.name}"
                )
                return chunks
            else:
                # Traditional processing for smaller files or non-text files
                raw_text = self._get_raw_text(file_path, extension)
                if not raw_text:
                    logger.error(f"Failed to extract text from {file_path.name}")
                    return []

                logger.info(
                    f"Extracted {len(raw_text)} characters from {file_path.name}"
                )

                # Chunk the text
                chunk_config = self.config["chunking"]
                chunks = chunk_text(
                    raw_text=raw_text,
                    file_hash=file_hash,
                    chunk_size=chunk_config["chunk_size"],
                    chunk_overlap=chunk_config["chunk_overlap"],
                )

                logger.info(f"Created {len(chunks)} chunks from {file_path.name}")
                return chunks

        except Exception as e:
            logger.error(
                f"Error parsing and chunking {file_path.name}: {e}", exc_info=True
            )
            return []

    def get_batch_processor(self) -> BatchProcessor:
        """
        Get the batch processor for adaptive batch processing.

        Returns:
            BatchProcessor instance or None if not available
        """
        return self.batch_processor

    def get_memory_estimate(self, file_path: Path) -> float:
        """
        Get memory usage estimate for processing a file.

        Args:
            file_path: Path to the file

        Returns:
            Estimated memory usage in MB
        """
        return self.streaming_processor.estimate_memory_usage(file_path)
