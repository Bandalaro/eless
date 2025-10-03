import logging
from typing import Dict, Any

# Import all core components
from .core.config_loader import ConfigLoader
from .core.state_manager import StateManager, FileStatus
from .core.archiver import Archiver

# Import the processing components
from .processing.file_scanner import FileScanner
from .processing.dispatcher import Dispatcher

# Import the embedding components
from .embedding.embedder import Embedder

# Import the database components
from .database.db_loader import DatabaseLoader

# NOTE: The db_loader needs concrete classes like ChromaDBConnector to be functional.

logger = logging.getLogger("ELESS.Pipeline")


class ElessPipeline:
    """
    The main class that orchestrates the entire ELESS process:
    Scanning -> Parsing & Chunking -> Embedding -> Database Loading.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes all core service components.
        """
        self.config = config

        # 1. Resilience Core
        self.state_manager = StateManager(config)
        self.archiver = Archiver(config)

        # 2. I/O and Processing
        self.scanner = FileScanner(config)
        self.dispatcher = Dispatcher(config, self.state_manager, self.archiver)

        # 3. Embedding
        # The Embedder initializes the ModelWrapper internally
        self.embedder = Embedder(config, self.state_manager, self.archiver)

        # 4. Database Loading
        # The DatabaseLoader will initialize concrete connectors (e.g., Chroma)
        self.db_loader = DatabaseLoader(config, self.state_manager, self.embedder)

        logger.info("ELESS pipeline components successfully initialized.")

    def run_process(self, source_path: str):
        """
        Executes the full pipeline for a new 'process' command.

        Args:
            source_path: The file or directory containing documents to process.
        """
        logger.info(f"Starting ELESS run for source: {source_path}")

        db_loader_initialized = False
        try:
            # Connect to databases before starting heavy lifting
            self.db_loader._initialize_connectors()
            if self.db_loader.active_connectors:
                db_loader_initialized = True

            # STAGE 1: Scanning and Dispatching
            # Generates dictionaries of {'path', 'hash', 'extension'}
            file_generator = self.scanner.scan_input(source_path)

            # STAGE 2: Parsing, Chunking, and Resume Check
            # Yields text chunks {text, metadata}
            chunk_generator = (
                chunk
                for file_data in file_generator
                for chunk in self.dispatcher.process_document(file_data)
            )

            # STAGE 3: Embedding and Archiving
            # Yields {text, metadata, vector}
            embedded_chunk_generator = self.embedder.embed_and_archive_chunks(
                chunk_generator
            )

            # STAGE 4: Database Loading and Final State Update
            self.db_loader.load_data(embedded_chunk_generator)

            logger.info("ELESS Pipeline execution finished successfully.")

        except FileNotFoundError as e:
            logger.error(f"Execution failed: {e}")
        except RuntimeError as e:
            logger.critical(
                f"A critical component failed to load or run (e.g., ModelWrapper): {e}"
            )
        except Exception as e:
            logger.error(f"An unexpected error halted the pipeline: {e}", exc_info=True)
        finally:
            if db_loader_initialized:
                self.db_loader.close()
            logger.info("Pipeline cleanup complete.")

    def run_resume(self):
        """
        Executes the 'resume' command.

        NOTE: Since all core resume logic is handled by the Dispatcher, Embedder,
        and StateManager automatically, the resume command is largely
        a simplified call to run_process, operating on the existing
        manifest/cache files to pick up where it left off.

        For a true resume, we'd need to re-read the original source path
        from the manifest, which we don't store globally yet. For this phase,
        we'll treat 'resume' as a flag to log the intent.
        """
        logger.info(
            "Resume command invoked. Resumption logic is handled internally by the Dispatcher."
        )
        logger.info(
            "To resume, typically the original source path would be re-provided or read from a session log."
        )
        # In a production system, this would load the 'last_source_path' from the cache/config
        # self.run_process(last_source_path)
