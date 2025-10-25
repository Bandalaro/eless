import logging
from typing import Dict, Any
import pickle
import json
from pathlib import Path
import numpy as np

# Import all core components
from .core.config_loader import ConfigLoader
from .core.state_manager import StateManager, FileStatus
from .core.archiver import Archiver
from .core.resource_monitor import ResourceMonitor

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

        # 5. Resource Monitoring
        self.resource_monitor = ResourceMonitor(config)

        logger.info("ELESS pipeline components successfully initialized.")

    def run_process(self, source_path: str):
        """
        Executes the full pipeline for a new 'process' command.

        Args:
            source_path: The file or directory containing documents to process.
        """
        db_loader_initialized = False
        logger.info(f"Starting ELESS run for source: {source_path}")
        try:
            self.db_loader.initialize_database_connections()
            db_loader_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            logger.warning(
                "Continuing with processing but data will not be persisted to databases"
            )

        try:
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
        Executes the 'resume' command by loading cached vectors into databases.
        """
        logger.info("Resume command invoked. Loading cached vectors into databases.")
        try:
            self.db_loader.initialize_database_connections()
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            return

        # Scan cache for chunk files
        cache_dir = Path(self.config["cache"]["directory"])
        chunk_files = list(cache_dir.glob("*.chunks.pkl"))
        if not chunk_files:
            logger.info("No cached chunks found for resume.")
            return

        processed_files = set()
        for chunks_path in chunk_files:
            file_hash = chunks_path.stem.replace(".chunks", "")
            try:
                # Load chunks
                with open(chunks_path, "rb") as f:
                    chunks = pickle.load(f)

                # Load vectors
                vectors_path = cache_dir / f"{file_hash}.vectors.npy"
                if not vectors_path.exists():
                    continue
                vectors = np.load(vectors_path)

                # Combine into format for db_loader
                vector_dicts = []
                for i, chunk in enumerate(chunks):
                    vector_dicts.append(
                        {
                            "id": f"{file_hash}-{i}",
                            "vector": vectors[i].tolist(),
                            "metadata": chunk["metadata"],
                        }
                    )

                if vector_dicts:
                    self.db_loader.batch_upsert(vector_dicts)
                    processed_files.add(file_hash)
                    logger.info(
                        f"Resumed loading {len(vector_dicts)} vectors for {file_hash[:8]}"
                    )

            except Exception as e:
                logger.error(f"Failed to resume file {file_hash[:8]}: {e}")

        # Update status to LOADED (preserve existing paths)
        for file_hash in processed_files:
            current_file_info = self.state_manager.manifest.get(file_hash, {})
            current_path = current_file_info.get("path", "N/A")
            self.state_manager.add_or_update_file(
                file_hash, FileStatus.LOADED, file_path=current_path
            )

        logger.info("Resume operation completed.")
