import click
import os
import yaml
import logging
from pathlib import Path
from typing import List, Optional

from eless.core.state_manager import StateManager
from eless.processing.file_scanner import FileScanner
from eless.processing.dispatcher import Dispatcher
from eless.embedding.model_loader import ModelLoader
from eless.embedding.embedder import Embedder
from eless.database.db_loader import DatabaseLoader as DBFactory
from eless.core.archiver import Archiver
from eless.core.logging_config import setup_logging
from eless.core.config_loader import ConfigLoader
from eless.core.resource_monitor import ResourceMonitor


# --- Configuration Loading ---
def get_default_config_path():
    """Get the default configuration file path if it exists."""
    # Try development location first
    dev_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config", "default_config.yaml"
    )
    if os.path.exists(dev_path):
        return dev_path

    # Try relative to current working directory
    cwd_path = os.path.join(os.getcwd(), "config", "default_config.yaml")
    if os.path.exists(cwd_path):
        return cwd_path

    # Return None if not found - ConfigLoader will use embedded defaults
    return None


DEFAULT_CONFIG_PATH = get_default_config_path()

# Available database options
AVAILABLE_DATABASES = ["chroma", "qdrant", "faiss", "postgresql", "cassandra"]


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option("--log-dir", type=click.Path(), help="Set custom log directory")
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Set custom cache directory for processed data",
)
@click.option(
    "--data-dir",
    type=click.Path(),
    help="Set custom data directory (parent for cache, logs, and databases)",
)
@click.pass_context
def cli(ctx, log_level, log_dir, cache_dir, data_dir):
    """
    ELESS - Evolving Low-resource Embedding and Storage System

    A resilient RAG data processing pipeline with multi-database support,
    comprehensive logging, and intelligent resource management.

    \b
    🚀 Quick Start:
      eless tutorial            # Interactive learning guide
      eless quickstart          # Show getting started guide
      eless init                # Run setup wizard
      eless doctor              # Check system health
      eless go docs/            # Simplest way to process documents

    \b
    📚 Processing Commands:
      eless process <path>      # Process documents (full options)
      eless process -i          # Interactive mode with prompts
      eless go <path>           # Quick process with auto-config
      eless demo                # Try with sample documents

    \b
    ⚙️  Configuration:
      eless template list       # List configuration templates
      eless template create     # Create config from template
      eless init                # Auto-detect and configure

    \b
    📊 Monitoring:
      eless status --all        # Check processing status
      eless monitor             # Real-time system monitoring
      eless sysinfo             # View system information

    \b
    💡 Get Help:
      eless <command> --help    # Detailed help for any command
      eless tutorial --quick    # 5-minute quick tutorial

    For more information, visit: https://github.com/Bandalaro/eless
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store CLI options for subcommands
    ctx.obj["log_level"] = log_level
    ctx.obj["log_dir"] = log_dir
    ctx.obj["cache_dir"] = cache_dir
    ctx.obj["data_dir"] = data_dir


@cli.command()
@click.argument("source", type=click.Path(exists=True), required=False)
@click.option(
    "--dry-run", is_flag=True, help="Perform a dry run without actual processing"
)
@click.option("--batch", is_flag=True, help="Enable batch processing mode")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Attempt to resume processing from the last checkpoint.",
)
@click.option(
    "--databases",
    "-db",
    multiple=True,
    type=click.Choice(AVAILABLE_DATABASES, case_sensitive=False),
    help=f'Select specific databases to use. Options: {", ".join(AVAILABLE_DATABASES)}. Can be specified multiple times.',
)
@click.option("--chunk-size", type=int, help="Override default chunk size")
@click.option("--batch-size", type=int, help="Override default batch size")
@click.option(
    "--parallel-workers",
    type=int,
    help="Number of parallel workers (0 to disable parallel processing)",
)
@click.option(
    "--parallel-mode",
    type=click.Choice(["thread", "process", "auto", "disable"]),
    help="Parallel processing mode: thread, process, auto, or disable",
)
@click.option(
    "--disable-parallel-files", is_flag=True, help="Disable parallel file processing"
)
@click.option(
    "--disable-parallel-embedding",
    is_flag=True,
    help="Disable parallel embedding generation",
)
@click.option(
    "--disable-parallel-db", is_flag=True, help="Disable parallel database operations"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Run in interactive mode with guided prompts",
)
@click.pass_context
def process(
    ctx,
    source,
    config,
    resume,
    databases,
    chunk_size,
    batch_size,
    parallel_workers,
    parallel_mode,
    disable_parallel_files,
    disable_parallel_embedding,
    disable_parallel_db,
    interactive,
):
    """
    Starts the full ELESS RAG data processing pipeline.
    SOURCE can be a file path, a folder, or a simple text string.

    Examples:

      # Process with default settings
      eless process /path/to/documents

      # Process with interactive prompts
      eless process --interactive

      # Process with specific databases
      eless process /path/to/documents --databases chroma --databases qdrant

      # Process with custom chunk size and resume
      eless process /path/to/documents --chunk-size 1000 --resume
    """
    # Handle interactive mode
    if interactive or source is None:
        from eless.interactive_mode import run_interactive_process

        options = run_interactive_process()
        if options is None:
            return

        # Apply interactive options
        source = options["source"]
        if options.get("database"):
            databases = (options["database"],)
        if options.get("chunk_size"):
            chunk_size = options["chunk_size"]
        if options.get("batch_size"):
            batch_size = options["batch_size"]
        if options.get("resume") is not None:
            resume = options["resume"]

    if not source:
        click.secho("Error: SOURCE is required", fg="red")
        click.echo("Run with --interactive for guided setup")
        return

    # Load and merge configuration
    try:
        # Use provided config file or fall back to embedded defaults
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}

        if chunk_size:
            cli_overrides["chunking"] = {"chunk_size": chunk_size}
        if batch_size:
            cli_overrides["databases"] = {"batch_size": batch_size}

        # Handle parallel processing overrides
        if any(
            [
                parallel_workers is not None,
                parallel_mode,
                disable_parallel_files,
                disable_parallel_embedding,
                disable_parallel_db,
            ]
        ):
            cli_overrides["parallel_processing"] = {}

            if parallel_workers is not None:
                if parallel_workers == 0:
                    # Disable all parallel processing
                    cli_overrides["parallel_processing"].update(
                        {
                            "enable_parallel_files": False,
                            "enable_parallel_chunks": False,
                            "enable_parallel_embedding": False,
                            "enable_parallel_database": False,
                        }
                    )
                else:
                    cli_overrides["parallel_processing"][
                        "max_workers"
                    ] = parallel_workers

            if parallel_mode:
                if parallel_mode == "disable":
                    cli_overrides["parallel_processing"].update(
                        {
                            "enable_parallel_files": False,
                            "enable_parallel_chunks": False,
                            "enable_parallel_embedding": False,
                            "enable_parallel_database": False,
                        }
                    )
                else:
                    cli_overrides["parallel_processing"]["mode"] = parallel_mode

            if disable_parallel_files:
                cli_overrides["parallel_processing"]["enable_parallel_files"] = False
            if disable_parallel_embedding:
                cli_overrides["parallel_processing"][
                    "enable_parallel_embedding"
                ] = False
            if disable_parallel_db:
                cli_overrides["parallel_processing"]["enable_parallel_database"] = False
        if ctx.obj.get("log_level"):
            cli_overrides["logging"] = {"level": ctx.obj["log_level"]}
        if ctx.obj.get("log_dir"):
            cli_overrides["logging"] = cli_overrides.get("logging", {})
            cli_overrides["logging"]["directory"] = ctx.obj["log_dir"]
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            # Set parent directory for all data storage
            data_dir = ctx.obj["data_dir"]
            if "logging" not in cli_overrides:
                cli_overrides["logging"] = {}
            if "cache" not in cli_overrides:
                cli_overrides["cache"] = {}

            # Set subdirectories under data_dir if not specifically overridden
            if not ctx.obj.get("log_dir"):
                cli_overrides["logging"]["directory"] = str(
                    Path(data_dir) / ".eless_logs"
                )
            if not ctx.obj.get("cache_dir"):
                cli_overrides["cache"]["directory"] = str(
                    Path(data_dir) / ".eless_cache"
                )

            # Update database paths to be under data_dir
            cli_overrides["databases"] = {"connections": {}}
            # Update ChromaDB path
            cli_overrides["databases"]["connections"]["chroma"] = {
                "type": "chroma",
                "path": str(Path(data_dir) / ".eless_chroma"),
            }
            # Update FAISS paths
            cli_overrides["databases"]["connections"]["faiss"] = {
                "type": "faiss",
                "index_path": str(Path(data_dir) / ".eless_faiss" / "index.faiss"),
                "metadata_path": str(Path(data_dir) / ".eless_faiss" / "metadata.json"),
            }

        app_config = config_loader.get_final_config(None, **cli_overrides)

    except Exception as e:
        click.secho(f"Error loading configuration: {e}", fg="red")
        return

    # Setup logging early
    try:
        eless_logger = setup_logging(app_config)
        logger = logging.getLogger("ELESS.CLI")
        logger.info(f"Starting ELESS pipeline on source: {source}")
    except Exception as e:
        click.secho(f"Error setting up logging: {e}", fg="red")
        return

    # Override database targets if specified in CLI
    if databases:
        app_config["databases"]["targets"] = list(databases)
        logger.info(f"Database targets overridden via CLI: {list(databases)}")

    try:
        # 2. Initialize Core Components (pre-model)
        logger.info("Initializing core components...")
        archiver = Archiver(app_config)
        state_manager = StateManager(app_config)
        resource_monitor = ResourceMonitor(app_config)
        scanner = FileScanner(app_config)
        dispatcher = Dispatcher(app_config, state_manager, archiver, resource_monitor)
        model_loader = ModelLoader(app_config)

        # --- Pipeline Execution ---

        # Checkpoint: Load the embedding model once
        logger.info("Loading embedding model...")
        embedding_model = model_loader._load_model()
        if embedding_model is None:
            click.secho("Failed to initialize embedding model. Exiting.", fg="red")
            logger.error("Failed to initialize embedding model")
            return
        logger.info("Embedding model loaded successfully")

        # 3. Initialize Post-Model Components
        logger.info("Initializing database connections...")
        embedder = Embedder(
            app_config, state_manager, archiver, model_loader, resource_monitor
        )
        db_factory = DBFactory(app_config, state_manager, model_loader.model)
        db_connectors = db_factory.active_connectors

        if not db_connectors:
            click.secho(
                "No database connections available. Check your configuration.", fg="red"
            )
            logger.error("No active database connections")
            return

        logger.info(f"Active database connections: {list(db_connectors.keys())}")
        click.echo(
            f"Connected to {len(db_connectors)} database(s): {', '.join(db_connectors.keys())}"
        )

        # A. Scan & Hash Input Files
        logger.info("Scanning input files...")
        file_metadata_list = scanner.scan_input(source)
        if not file_metadata_list:
            click.secho("No processable files found.", fg="yellow")
            logger.warning("No processable files found")
            return

        total_files = len(file_metadata_list)
        click.echo(f"Found {total_files} file(s) to process.")
        logger.info(f"Found {total_files} files to process")

        # B. Main Processing Loop (Resumption Logic Applied Here)
        success_count = 0
        error_count = 0

        for i, file_meta in enumerate(file_metadata_list):
            file_id = file_meta.get("file_id") or file_meta.get(
                "hash"
            )  # Support both formats
            file_path = str(file_meta["path"])
            status = state_manager.get_status(file_id)

            click.echo(
                f"\n--- Processing File {i+1}/{total_files}: {os.path.basename(file_path)} (Status: {status}) ---"
            )
            logger.info(
                f"Processing file {i+1}/{total_files}: {file_path} (Status: {status})"
            )

            if status == "LOADED":
                click.secho("Status is LOADED. Skipping file.", fg="green")
                logger.debug(f"Skipping already loaded file: {file_path}")
                success_count += 1
                continue

            try:
                # Step 1: Chunking (Parsing & Splitting)
                if status == "PENDING" or (status == "EMBEDDED" and not resume):
                    logger.debug(f"Starting chunking for file: {file_path}")

                    # Check memory before processing
                    estimated_memory = dispatcher.get_memory_estimate(Path(file_path))
                    logger.info(
                        f"Estimated memory for {os.path.basename(file_path)}: {estimated_memory:.1f}MB"
                    )

                    chunks = dispatcher.parse_and_chunk(Path(file_path), file_meta)
                    state_manager.add_or_update_file(
                        file_id, "CHUNKED", file_path=file_path
                    )
                elif status == "EMBEDDED" and resume:
                    click.secho(
                        "Status is EMBEDDED. Resuming from Vector Loading step.",
                        fg="yellow",
                    )
                    logger.info("Resuming from EMBEDDED status")
                    # Load cached vectors instead of re-running the embedding step
                    chunks = archiver.load_chunks(file_id) or []
                    vectors = []
                else:  # Resume from CHUNKED state
                    click.secho(
                        "Status is CHUNKED. Resuming from Embedding step.", fg="yellow"
                    )
                    logger.info("Resuming from CHUNKED status")
                    # Load chunks from cache
                    chunks = archiver.load_chunks(file_id) or []

                if not chunks:
                    click.secho(
                        f"Could not extract chunks from {file_path}. Skipping.",
                        fg="red",
                    )
                    logger.error(f"Failed to extract chunks from {file_path}")
                    error_count += 1
                    continue

                logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")

                # Step 2: Embedding (Vectorization) using new Embedder
                if status != "EMBEDDED":
                    click.echo(f"Generating embeddings for {len(chunks)} chunks...")
                    logger.info(f"Generating embeddings for {len(chunks)} chunks")

                    try:
                        # Use the new embedder with streaming and adaptive batching support
                        embedded_chunks = embedder.embed_file_chunks(file_id, chunks)

                        if not embedded_chunks:
                            click.secho(
                                f"Failed to generate embeddings for {file_path}",
                                fg="red",
                            )
                            error_count += 1
                            continue

                        # Extract vectors for database loading
                        vectors = [
                            (
                                chunk["vector"].tolist()
                                if hasattr(chunk["vector"], "tolist")
                                else chunk["vector"]
                            )
                            for chunk in embedded_chunks
                        ]
                        chunks = embedded_chunks  # Update chunks with vectors

                        click.secho("Embedding successful and cached.", fg="cyan")
                        logger.info("Embeddings generated successfully")
                    except Exception as e:
                        click.secho(f"Failed to generate embeddings: {e}", fg="red")
                        logger.error(f"Embedding failed for {file_path}: {e}")
                        error_count += 1
                        continue
                else:
                    # Load cached vectors
                    cached_vectors = archiver.load_vectors(file_id)
                    if cached_vectors is not None:
                        vectors = (
                            cached_vectors.tolist()
                            if hasattr(cached_vectors, "tolist")
                            else cached_vectors
                        )
                        logger.info(
                            f"Loaded {len(vectors)} cached vectors for {file_path}"
                        )
                    else:
                        logger.warning(
                            f"Status was EMBEDDED but no cached vectors found for {file_path}"
                        )
                        continue

                # Step 3: Loading (Upsert to all Databases)
                click.echo(f"Loading vectors into {len(db_connectors)} database(s)...")
                logger.info(f"Loading vectors into {len(db_connectors)} databases")

                all_success = True
                for name, connector in db_connectors.items():
                    try:
                        # Create batch data for upsert
                        batch_data = []
                        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                            batch_data.append(
                                {
                                    "id": f"{file_id}_{idx}",
                                    "vector": vector,
                                    "metadata": {
                                        "file_id": file_id,
                                        "file_path": str(file_path),
                                        "chunk_index": idx,
                                        "text": chunk["text"][
                                            :200
                                        ],  # Truncated text for metadata
                                        **chunk.get("metadata", {}),
                                    },
                                }
                            )

                        connector.upsert_batch(batch_data)
                        click.secho(
                            f"    ✓ Loaded successfully into {name}", fg="green"
                        )
                        logger.info(f"Successfully loaded into {name}")
                    except Exception as db_e:
                        click.secho(
                            f"    ✗ Failed to load into {name}: {db_e}", fg="red"
                        )
                        logger.error(f"Failed to load into {name}: {db_e}")
                        all_success = False

                # Final Checkpoint
                if all_success:
                    state_manager.add_or_update_file(
                        file_id, "LOADED", file_path=file_path
                    )
                    click.secho(
                        f"File {os.path.basename(file_path)} successfully LOADED.",
                        fg="green",
                    )
                    logger.info(f"File successfully loaded: {file_path}")
                    success_count += 1
                else:
                    logger.warning(f"File partially loaded: {file_path}")
                    error_count += 1

            except Exception as e:
                click.secho(f"Error processing {file_path}: {e}", fg="red")
                logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                error_count += 1

        # Final summary
        click.echo(f"\n=== Processing Complete ===")
        click.echo(f"Total files: {total_files}")
        click.secho(f"Successful: {success_count}", fg="green")
        if error_count > 0:
            click.secho(f"Errors: {error_count}", fg="red")

        logger.info(
            f"Processing complete. Success: {success_count}, Errors: {error_count}"
        )

        # Cleanup
        try:
            db_factory.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")

    except Exception as e:
        click.secho(f"Pipeline error: {e}", fg="red")
        logger.error(f"Pipeline error: {e}", exc_info=True)


@cli.command()
@click.argument("file_id", required=False)
@click.option("--all", is_flag=True, help="Show status of all tracked files")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.pass_context
def status(ctx, file_id, all, config):
    """Checks the processing status of files."""
    try:
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}
        if ctx.obj.get("log_level"):
            cli_overrides["logging"] = {"level": ctx.obj["log_level"]}
        if ctx.obj.get("log_dir"):
            cli_overrides["logging"] = cli_overrides.get("logging", {})
            cli_overrides["logging"]["directory"] = ctx.obj["log_dir"]
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            # Apply data_dir overrides similar to process command
            data_dir = ctx.obj["data_dir"]
            if "logging" not in cli_overrides:
                cli_overrides["logging"] = {}
            if "cache" not in cli_overrides:
                cli_overrides["cache"] = {}

            if not ctx.obj.get("log_dir"):
                cli_overrides["logging"]["directory"] = str(
                    Path(data_dir) / ".eless_logs"
                )
            if not ctx.obj.get("cache_dir"):
                cli_overrides["cache"]["directory"] = str(
                    Path(data_dir) / ".eless_cache"
                )

        app_config = config_loader.get_final_config(None, **cli_overrides)
        state_manager = StateManager(app_config)

        if all:
            # Show all files
            all_hashes = state_manager.get_all_hashes()
            if not all_hashes:
                click.echo("No files tracked yet.")
                return

            click.echo(f"\nTracked files ({len(all_hashes)}):")
            click.echo("-" * 80)
            for hash_id in all_hashes:
                file_status = state_manager.get_status(hash_id)
                file_info = state_manager.manifest.get(hash_id, {})
                file_path = file_info.get("path", "Unknown")
                timestamp = file_info.get("timestamp", "Unknown")

                color = (
                    "green"
                    if file_status == "LOADED"
                    else "yellow" if file_status in ["CHUNKED", "EMBEDDED"] else "red"
                )
                click.secho(
                    f"ID: {hash_id[:12]}... | Status: {file_status:>10} | {os.path.basename(file_path)}",
                    fg=color,
                )
                click.echo(f"    Path: {file_path}")
                click.echo(f"    Last Updated: {timestamp}")
                click.echo()
        elif file_id:
            # Show specific file
            file_status = state_manager.get_status(file_id)
            file_info = state_manager.manifest.get(file_id, {})

            click.echo(f"File ID: {file_id}")
            color = (
                "green"
                if file_status == "LOADED"
                else "yellow" if file_status in ["CHUNKED", "EMBEDDED"] else "red"
            )
            click.secho(f"Current Status: {file_status}", fg=color)

            if file_info:
                click.echo(f"Path: {file_info.get('path', 'Unknown')}")
                click.echo(f"Last Updated: {file_info.get('timestamp', 'Unknown')}")
                metadata = file_info.get("metadata", {})
                if metadata:
                    click.echo("Metadata:")
                    for key, value in metadata.items():
                        click.echo(f"  {key}: {value}")
        else:
            # Show summary
            all_hashes = state_manager.get_all_hashes()
            if not all_hashes:
                click.echo("No files tracked yet.")
                return

            # Count by status
            status_counts = {}
            for hash_id in all_hashes:
                file_status = state_manager.get_status(hash_id)
                status_counts[file_status] = status_counts.get(file_status, 0) + 1

            click.echo("\n=== ELESS Status Summary ===")
            click.echo(f"Total files tracked: {len(all_hashes)}")
            click.echo("\nStatus breakdown:")
            for status, count in sorted(status_counts.items()):
                color = (
                    "green"
                    if status == "LOADED"
                    else "yellow" if status in ["CHUNKED", "EMBEDDED"] else "red"
                )
                click.secho(f"  {status}: {count}", fg=color)

            click.echo(
                "\nUse --all to see all files or provide a file_id to see specific file details."
            )

    except Exception as e:
        click.secho(f"Error checking status: {e}", fg="red")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.option(
    "--test-db",
    type=click.Choice(AVAILABLE_DATABASES, case_sensitive=False),
    help="Test connection to a specific database",
)
@click.pass_context
def test(ctx, config, test_db):
    """Test database connections and system components."""
    try:
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}
        if ctx.obj.get("log_level"):
            cli_overrides["logging"] = {"level": ctx.obj["log_level"]}
        if ctx.obj.get("log_dir"):
            cli_overrides["logging"] = cli_overrides.get("logging", {})
            cli_overrides["logging"]["directory"] = ctx.obj["log_dir"]
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            # Apply data_dir overrides
            data_dir = ctx.obj["data_dir"]
            if "logging" not in cli_overrides:
                cli_overrides["logging"] = {}
            if "cache" not in cli_overrides:
                cli_overrides["cache"] = {}

            if not ctx.obj.get("log_dir"):
                cli_overrides["logging"]["directory"] = str(
                    Path(data_dir) / ".eless_logs"
                )
            if not ctx.obj.get("cache_dir"):
                cli_overrides["cache"]["directory"] = str(
                    Path(data_dir) / ".eless_cache"
                )

        app_config = config_loader.get_final_config(None, **cli_overrides)

        # Setup logging
        eless_logger = setup_logging(app_config)
        logger = logging.getLogger("ELESS.Test")

        click.echo("=== ELESS System Test ===")

        # Test embedding model
        click.echo("\n1. Testing embedding model...")
        try:
            from eless.embedding.model_loader import ModelLoader

            model_loader = ModelLoader(app_config)
            embedding_model = model_loader._load_model()
            if embedding_model:
                # Test with sample text
                test_vectors = embedding_model.encode(
                    ["This is a test sentence."], convert_to_tensor=False
                )
                click.secho(
                    "   ✓ Embedding model loaded and tested successfully", fg="green"
                )
                click.echo(f"   Vector dimension: {len(test_vectors[0])}")
                logger.info("Embedding model test passed")
            else:
                click.secho("   ✗ Failed to load embedding model", fg="red")
                logger.error("Embedding model test failed")
        except Exception as e:
            click.secho(f"   ✗ Embedding model test failed: {e}", fg="red")
            logger.error(f"Embedding model test failed: {e}")

        # Test databases
        click.echo("\n2. Testing database connections...")
        if test_db:
            # Test specific database
            app_config["databases"]["targets"] = [test_db]

        try:
            from eless.database.db_loader import DatabaseLoader

            state_manager = StateManager(app_config)
            db_loader = DatabaseLoader(app_config, state_manager, embedding_model)

            if db_loader.active_connectors:
                for name, connector in db_loader.active_connectors.items():
                    try:
                        if connector.check_connection():
                            click.secho(
                                f"   ✓ {name} connection successful", fg="green"
                            )
                            logger.info(f"{name} connection test passed")
                        else:
                            click.secho(f"   ✗ {name} connection failed", fg="red")
                            logger.error(f"{name} connection test failed")
                    except Exception as e:
                        click.secho(f"   ✗ {name} connection error: {e}", fg="red")
                        logger.error(f"{name} connection error: {e}")
            else:
                click.secho("   ✗ No active database connections", fg="red")
                logger.warning("No active database connections")

            db_loader.close()
        except Exception as e:
            click.secho(f"   ✗ Database test failed: {e}", fg="red")
            logger.error(f"Database test failed: {e}")

        # Test file operations
        click.echo("\n3. Testing file operations...")
        try:
            cache_dir = Path(app_config["cache"]["directory"])
            cache_dir.mkdir(parents=True, exist_ok=True)

            test_file = cache_dir / "test_write.txt"
            test_file.write_text("test")
            test_content = test_file.read_text()
            test_file.unlink()

            if test_content == "test":
                click.secho("   ✓ File operations working", fg="green")
                logger.info("File operations test passed")
            else:
                click.secho("   ✗ File operations failed", fg="red")
                logger.error("File operations test failed")
        except Exception as e:
            click.secho(f"   ✗ File operations test failed: {e}", fg="red")
            logger.error(f"File operations test failed: {e}")

        click.echo("\n=== Test Complete ===")

    except Exception as e:
        click.secho(f"Test error: {e}", fg="red")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.option("--days", type=int, default=30, help="Clean logs older than N days")
@click.pass_context
def logs(ctx, config, days):
    """Manage log files."""
    try:
        # Use provided config file or fall back to embedded defaults
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}
        if ctx.obj.get("log_level"):
            cli_overrides["logging"] = {"level": ctx.obj["log_level"]}
        if ctx.obj.get("log_dir"):
            cli_overrides["logging"] = cli_overrides.get("logging", {})
            cli_overrides["logging"]["directory"] = ctx.obj["log_dir"]
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            # Apply data_dir overrides
            data_dir = ctx.obj["data_dir"]
            if "logging" not in cli_overrides:
                cli_overrides["logging"] = {}

            if not ctx.obj.get("log_dir"):
                cli_overrides["logging"]["directory"] = str(
                    Path(data_dir) / ".eless_logs"
                )

        app_config = config_loader.get_final_config(None, **cli_overrides)

        # Setup logging to get log directory
        eless_logger = setup_logging(app_config)

        # Show log files
        log_files = eless_logger.get_log_files()
        if log_files:
            click.echo("\n=== Log Files ===")
            total_size = 0
            for log_file in sorted(log_files):
                size = log_file.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                modified_time = log_file.stat().st_mtime
                import datetime

                mod_date = datetime.datetime.fromtimestamp(modified_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                click.echo(f"{log_file.name:<20} | {size_mb:>6.2f} MB | {mod_date}")

            click.echo(f"\nTotal log size: {total_size / (1024 * 1024):.2f} MB")

            # Clean old logs if requested
            if days > 0:
                click.echo(f"\nCleaning logs older than {days} days...")
                removed = eless_logger.cleanup_old_logs(days)
                if removed:
                    click.secho(f"Removed {len(removed)} old log files", fg="green")
                else:
                    click.echo("No old log files to remove")
        else:
            click.echo("No log files found")

    except Exception as e:
        click.secho(f"Error managing logs: {e}", fg="red")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.pass_context
def config_info(ctx, config):
    """Show current configuration information."""
    try:
        # Use provided config file or fall back to embedded defaults
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        app_config = config_loader.get_final_config()

        click.echo("=== ELESS Configuration ===")
        config_source = str(config_path) if config_path else "Embedded defaults"
        click.echo(f"Config source: {config_source}")

        # Show key configuration sections
        sections = {
            "Cache": app_config.get("cache", {}),
            "Logging": app_config.get("logging", {}),
            "Embedding": app_config.get("embedding", {}),
            "Chunking": app_config.get("chunking", {}),
            "Databases": {
                "targets": app_config.get("databases", {}).get("targets", []),
                "batch_size": app_config.get("databases", {}).get("batch_size"),
            },
        }

        for section_name, section_config in sections.items():
            click.echo(f"\n{section_name}:")
            for key, value in section_config.items():
                if isinstance(value, list):
                    click.echo(f"  {key}: {', '.join(str(v) for v in value)}")
                else:
                    click.echo(f"  {key}: {value}")

        # Show available databases
        click.echo(f"\nAvailable Databases: {', '.join(AVAILABLE_DATABASES)}")

    except Exception as e:
        click.secho(f"Error reading configuration: {e}", fg="red")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.option("--stats", is_flag=True, help="Show cache statistics")
@click.option("--cleanup", is_flag=True, help="Clean corrupted cache files")
@click.option("--evict", is_flag=True, help="Evict old cache files if needed")
@click.option("--clear", is_flag=True, help="Clear entire cache (WARNING: destructive)")
@click.pass_context
def cache(ctx, config, stats, cleanup, evict, clear):
    """Manage cache files and storage."""
    try:
        # Load configuration with directory overrides
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}

        # Apply directory overrides
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            data_dir = ctx.obj["data_dir"]
            if "cache" not in cli_overrides:
                cli_overrides["cache"] = {}
            if not ctx.obj.get("cache_dir"):
                cli_overrides["cache"]["directory"] = str(
                    Path(data_dir) / ".eless_cache"
                )

        app_config = config_loader.get_final_config(None, **cli_overrides)

        # Initialize cache manager
        from eless.core.cache_manager import SmartCacheManager

        cache_mgr = SmartCacheManager(app_config)

        if stats:
            # Show cache statistics
            stats_data = cache_mgr.get_cache_stats()
            click.echo("\n=== Cache Statistics ===")
            click.echo(f"Cache Directory: {cache_mgr.cache_dir}")
            click.echo(
                f"Current Size: {stats_data['size_mb']:.1f} MB / {stats_data['max_size_mb']} MB"
            )
            click.echo(f"Files: {stats_data['file_count']} / {stats_data['max_files']}")
            click.echo(f"Utilization: {stats_data['utilization_percent']:.1f}%")
            click.echo(f"Tracked Accesses: {stats_data['tracked_accesses']}")

            # Show color-coded status
            if stats_data["utilization_percent"] > 90:
                click.secho("Status: CRITICAL - Cache nearly full", fg="red")
            elif stats_data["utilization_percent"] > 75:
                click.secho("Status: WARNING - Cache getting full", fg="yellow")
            else:
                click.secho("Status: OK", fg="green")

        elif cleanup:
            # Clean corrupted files
            click.echo("Cleaning corrupted cache files...")
            corrupted = cache_mgr.cleanup_corrupted_files()
            if corrupted:
                click.secho(
                    f"Cleaned {len(corrupted)} corrupted cache entries", fg="green"
                )
            else:
                click.echo("No corrupted files found")

        elif evict:
            # Evict old files
            click.echo("Checking if cache eviction is needed...")
            if cache_mgr.should_evict():
                evicted = cache_mgr.evict_lru_items()
                click.secho(f"Evicted {len(evicted)} old cache entries", fg="green")
                new_stats = cache_mgr.get_cache_stats()
                click.echo(f"New cache size: {new_stats['size_mb']:.1f} MB")
            else:
                click.echo("No eviction needed")

        elif clear:
            # Clear entire cache
            if click.confirm(
                "WARNING: This will delete all cached data. Are you sure?"
            ):
                if cache_mgr.clear_cache():
                    click.secho("Cache cleared successfully", fg="green")
                else:
                    click.secho("Failed to clear cache", fg="red")
            else:
                click.echo("Cache clear cancelled")

        else:
            # Default: show stats and perform auto-maintenance
            click.echo("=== Cache Management ===")
            stats_data = cache_mgr.get_cache_stats()
            click.echo(
                f"Cache: {stats_data['size_mb']:.1f}MB/{stats_data['max_size_mb']}MB ({stats_data['utilization_percent']:.1f}%)"
            )

            # Auto-maintenance
            click.echo("\nPerforming automatic maintenance...")
            cache_mgr.auto_maintain()
            click.secho("Maintenance complete", fg="green")

    except Exception as e:
        click.secho(f"Error managing cache: {e}", fg="red")


@cli.group()
@click.pass_context
def config(ctx):
    """Configuration management commands."""
    pass


@config.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="eless_config.yaml",
    help="Output configuration file path",
)
@click.pass_context
def wizard(ctx, output):
    """Interactive configuration wizard."""
    try:
        from eless.core.config_wizard import ConfigWizard

        wizard = ConfigWizard()
        config_dict = wizard.run_wizard()

        output_path = Path(output)
        if wizard.save_config(output_path):
            click.echo("\n🎉 Setup complete! You can now start processing documents.")

    except Exception as e:
        click.secho(f"Configuration wizard error: {e}", fg="red")


@config.command()
@click.argument(
    "preset", type=click.Choice(["minimal", "standard", "high-end", "docker"])
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="eless_config.yaml",
    help="Output configuration file path",
)
@click.pass_context
def init(ctx, preset, output):
    """Generate preset configuration for different system types."""
    try:
        from eless.core.config_wizard import generate_preset_config
        import yaml

        config_dict = generate_preset_config(preset)
        output_path = Path(output)

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        click.echo(f"✨ Generated {preset} configuration: {output_path}")
        click.echo(f"\nTo use this configuration:")
        click.echo(f"   eless --config {output_path} process your_documents/")

    except Exception as e:
        click.secho(f"Error generating preset config: {e}", fg="red")


@config.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, config_file):
    """Validate a configuration file."""
    try:
        import yaml
        from pathlib import Path

        # Load and parse config
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)

        # Basic structure validation
        required_sections = ["cache", "logging", "embedding", "chunking", "databases"]
        missing_sections = []

        for section in required_sections:
            if section not in config_dict:
                missing_sections.append(section)

        if missing_sections:
            click.secho(
                f"❌ Missing required sections: {', '.join(missing_sections)}", fg="red"
            )
            return

        # Validate paths exist or can be created
        paths_to_check = [
            config_dict.get("cache", {}).get("directory"),
            config_dict.get("logging", {}).get("directory"),
        ]

        for path_str in paths_to_check:
            if path_str:
                path = Path(path_str)
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    click.secho(f"✓ Path validated: {path}", fg="green")
                except Exception as e:
                    click.secho(f"❌ Path error {path}: {e}", fg="red")

        # Check numeric ranges
        batch_size = config_dict.get("embedding", {}).get("batch_size", 32)
        if not (1 <= batch_size <= 1000):
            click.secho(
                f"⚠️  Warning: batch_size {batch_size} may be too large/small",
                fg="yellow",
            )

        cache_size = config_dict.get("cache", {}).get("max_size_mb", 1024)
        if cache_size < 100:
            click.secho(
                f"⚠️  Warning: cache size {cache_size}MB may be too small", fg="yellow"
            )

        click.secho(f"✅ Configuration file {config_file} is valid!", fg="green")

    except Exception as e:
        click.secho(f"❌ Configuration validation failed: {e}", fg="red")


@config.command(name="auto-detect")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="auto_config.yaml",
    help="Output configuration file path",
)
@click.pass_context
def auto_detect(ctx, output):
    """Auto-detect optimal configuration for current system."""
    try:
        import psutil
        import yaml

        # Detect system resources
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_cores = psutil.cpu_count()
        disk_gb = psutil.disk_usage("/").free / (1024**3)

        click.echo(
            f"🔍 Detected system: {memory_gb:.1f}GB RAM, {cpu_cores} CPU cores, {disk_gb:.1f}GB free disk"
        )

        # Determine optimal preset
        if memory_gb < 4:
            preset = "minimal"
        elif memory_gb < 8:
            preset = "standard"
        else:
            preset = "high-end"

        click.echo(f"💡 Recommended configuration: {preset}")

        # Generate config
        from eless.core.config_wizard import generate_preset_config

        config_dict = generate_preset_config(preset)

        # Auto-adjust based on detected resources
        if memory_gb > 16:
            config_dict["embedding"]["batch_size"] = min(
                128, config_dict["embedding"]["batch_size"] * 2
            )
            config_dict["cache"]["max_size_mb"] = min(
                8192, config_dict["cache"]["max_size_mb"] * 2
            )

        # Save config
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        click.echo(f"✨ Auto-generated configuration saved to: {output_path}")
        click.echo(f"\nKey settings:")
        click.echo(f"   Embedding batch size: {config_dict['embedding']['batch_size']}")
        click.echo(f"   Cache limit: {config_dict['cache']['max_size_mb']} MB")
        click.echo(
            f"   Memory warning: {config_dict['resource_limits']['memory_warning_percent']}%"
        )

    except Exception as e:
        click.secho(f"Auto-detection failed: {e}", fg="red")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.option(
    "--interval", "-i", type=int, default=5, help="Update interval in seconds"
)
@click.option(
    "--duration",
    "-d",
    type=int,
    default=0,
    help="Monitoring duration in seconds (0 = infinite)",
)
@click.pass_context
def monitor(ctx, config, interval, duration):
    """Real-time system monitoring for ELESS processing."""
    try:
        import time
        from datetime import datetime

        # Load configuration
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        app_config = config_loader.get_final_config()

        # Initialize resource monitor
        from eless.core.resource_monitor import ResourceMonitor
        from eless.core.cache_manager import SmartCacheManager

        resource_monitor = ResourceMonitor(app_config)
        cache_manager = SmartCacheManager(app_config)

        click.echo("\n🖥️  ELESS System Monitor")
        click.echo("Press Ctrl+C to stop\n")

        start_time = time.time()

        while True:
            # Clear screen (works on most terminals)
            click.echo("\033[2J\033[H", nl=False)

            # Header
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elapsed = int(time.time() - start_time)
            click.echo(f"ELESS Monitor - {current_time} (Running: {elapsed}s)")
            click.echo("=" * 60)

            # System Resources
            summary = resource_monitor.get_system_summary()
            click.echo("\n📊 System Resources:")

            # Memory status with color
            memory_color = (
                "red"
                if summary["memory_percent"] > 90
                else "yellow" if summary["memory_percent"] > 80 else "green"
            )
            click.secho(
                f"   Memory: {summary['memory_percent']:.1f}% ({summary['memory_pressure']}) - {summary['memory_available_mb']:.0f}MB free",
                fg=memory_color,
            )

            # CPU status
            cpu_color = (
                "red"
                if summary["cpu_percent"] > 90
                else "yellow" if summary["cpu_percent"] > 80 else "green"
            )
            click.secho(
                f"   CPU: {summary['cpu_percent']:.1f}% - Trend: {summary['cpu_trend']}",
                fg=cpu_color,
            )

            # Disk usage
            disk_color = (
                "red"
                if summary["disk_usage_percent"] > 90
                else "yellow" if summary["disk_usage_percent"] > 80 else "green"
            )
            click.secho(
                f"   Disk: {summary['disk_usage_percent']:.1f}% used", fg=disk_color
            )

            # Processing status
            click.echo("\n⚙️  Processing Status:")
            if summary["should_throttle"]:
                click.secho("   Status: THROTTLED - Resources constrained", fg="red")
            else:
                click.secho("   Status: READY - Resources available", fg="green")

            click.echo(
                f"   Recommended batch size: {summary['recommended_batch_size']}"
            )

            # Cache status
            cache_stats = cache_manager.get_cache_stats()
            click.echo("\n💾 Cache Status:")
            cache_color = (
                "red"
                if cache_stats["utilization_percent"] > 90
                else "yellow" if cache_stats["utilization_percent"] > 75 else "green"
            )
            click.secho(
                f"   Size: {cache_stats['size_mb']:.1f}MB / {cache_stats['max_size_mb']}MB ({cache_stats['utilization_percent']:.1f}%)",
                fg=cache_color,
            )
            click.echo(
                f"   Files: {cache_stats['file_count']} / {cache_stats['max_files']}"
            )

            # Performance recommendations
            click.echo("\n💡 Recommendations:")
            if summary["memory_percent"] > 85:
                click.secho(
                    "   • Consider reducing batch size or clearing cache", fg="yellow"
                )
            if cache_stats["utilization_percent"] > 90:
                click.secho(
                    "   • Cache nearly full - run 'eless cache --evict'", fg="yellow"
                )
            if summary["cpu_percent"] > 90:
                click.secho(
                    "   • High CPU usage - consider pausing processing", fg="yellow"
                )
            if summary["memory_percent"] < 50 and summary["cpu_percent"] < 50:
                click.secho(
                    "   • System resources available - can increase batch sizes",
                    fg="green",
                )

            # Sleep or exit
            time.sleep(interval)

            # Check duration limit
            if duration > 0 and (time.time() - start_time) >= duration:
                break

    except KeyboardInterrupt:
        click.echo("\n\nMonitoring stopped.")
    except Exception as e:
        click.secho(f"Monitoring error: {e}", fg="red")


@cli.command()
@click.pass_context
def version(ctx):
    """Show ELESS version information."""
    click.echo("ELESS version 1.0.0")
    click.echo("Evolving Low-resource Embedding and Storage System")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom configuration file.",
)
@click.pass_context
def resume(ctx, config):
    """Resume processing from the last checkpoint."""
    try:
        config_path = (
            Path(config)
            if config
            else (Path(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH else None)
        )
        config_loader = ConfigLoader(config_path)
        cli_overrides = {}
        if ctx.obj.get("log_level"):
            cli_overrides["logging"] = {"level": ctx.obj["log_level"]}
        if ctx.obj.get("log_dir"):
            cli_overrides["logging"] = cli_overrides.get("logging", {})
            cli_overrides["logging"]["directory"] = ctx.obj["log_dir"]
        if ctx.obj.get("cache_dir"):
            cli_overrides["cache"] = {"directory": ctx.obj["cache_dir"]}
        if ctx.obj.get("data_dir"):
            data_dir = ctx.obj["data_dir"]
            if "logging" not in cli_overrides:
                cli_overrides["logging"] = {}
            if "cache" not in cli_overrides:
                cli_overrides["cache"] = {}

            if not ctx.obj.get("log_dir"):
                cli_overrides["logging"]["directory"] = str(
                    Path(data_dir) / ".eless_logs"
                )
            if not ctx.obj.get("cache_dir"):
                cli_overrides["cache"]["directory"] = str(
                    Path(data_dir) / ".eless_cache"
                )

        app_config = config_loader.get_final_config(None, **cli_overrides)

        # Setup logging
        eless_logger = setup_logging(app_config)
        logger = logging.getLogger("ELESS.CLI")

        # Initialize components
        state_manager = StateManager(app_config)
        archiver = Archiver(app_config)

        # Find files that need resuming
        all_hashes = state_manager.get_all_hashes()
        pending_files = []

        for file_hash in all_hashes:
            status = state_manager.get_status(file_hash)
            if status in ["PENDING", "CHUNKED", "EMBEDDED"]:
                file_info = state_manager.manifest.get(file_hash, {})
                file_path = file_info.get("path")
                if file_path and Path(file_path).exists():
                    pending_files.append((file_hash, file_path, status))

        if not pending_files:
            click.echo("No files found that need resuming.")
            return

        click.echo(f"Found {len(pending_files)} file(s) to resume:")
        for file_hash, file_path, status in pending_files:
            click.echo(f"  {os.path.basename(file_path)} - Status: {status}")

        # Resume processing logic would go here
        # For now, just show what would be resumed
        click.echo("\nResume functionality not yet implemented.")
        click.echo("Use 'eless process --resume <source>' instead.")

    except Exception as e:
        click.secho(f"Error resuming processing: {e}", fg="red")


@cli.command()
def doctor():
    """
    Run system health check and diagnose issues.

    Checks Python version, dependencies, available databases,
    system resources, and configuration validity.

    Example:
        eless doctor
    """
    try:
        from eless.health_check import run_health_check

        run_health_check(verbose=True)
    except Exception as e:
        click.secho(f"Error running health check: {e}", fg="red")


@cli.command()
@click.option(
    "--preset",
    type=click.Choice(["minimal", "balanced", "performance"]),
    default="balanced",
    help="Configuration preset to use",
)
def init(preset):
    """
    Interactive setup wizard for first-time configuration.

    Detects system resources and creates an optimal configuration
    file based on your hardware.

    Presets:
      minimal     - Low resource usage (256MB RAM, batch 8)
      balanced    - Auto-detected optimal settings (default)
      performance - Maximum performance (requires good hardware)

    Example:
        eless init
        eless init --preset minimal
    """
    try:
        from eless.auto_config import (
            detect_system_resources,
            generate_auto_config,
            get_preset_config,
            print_system_info,
        )

        click.secho("\n🚀 ELESS Setup Wizard", fg="blue", bold=True)
        click.secho("=" * 60, fg="blue")

        # Show system info
        print_system_info()

        # Get config based on preset
        if preset == "balanced":
            click.secho("Generating auto-detected configuration...\n", fg="yellow")
            config = generate_auto_config()
        else:
            click.secho(f"Using '{preset}' preset configuration...\n", fg="yellow")
            config = get_preset_config(preset)

        # Show what will be configured
        click.secho("📝 Configuration Preview:", fg="green", bold=True)
        click.secho(f"  Batch size: {config['embedding']['batch_size']}")
        click.secho(f"  Device: {config['embedding']['device']}")
        click.secho(f"  Memory limit: {config['resource_limits']['max_memory_mb']}MB")
        click.secho(f"  Workers: {config['parallel']['max_workers']}")
        click.secho()

        if click.confirm("Save this configuration?", default=True):
            # Save to user's home directory
            config_dir = Path.home() / ".eless"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.yaml"

            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

            click.secho(
                f"\n✓ Configuration saved to: {config_path}", fg="green", bold=True
            )
            click.secho("\n📚 Next steps:", fg="blue")
            click.secho("  1. Test your setup: eless doctor")
            click.secho("  2. Process documents: eless process /path/to/documents")
            click.secho("  3. Check status: eless status\n")
        else:
            click.secho("Setup cancelled.", fg="yellow")

    except Exception as e:
        click.secho(f"Error during setup: {e}", fg="red")


@cli.command()
def quickstart():
    """
    Quick start guide for new users.

    Shows a step-by-step guide to get started with ELESS,
    including installation verification, setup, and first run.

    Example:
        eless quickstart
    """
    click.secho("\n" + "=" * 60, fg="blue", bold=True)
    click.secho("  🚀 ELESS Quick Start Guide", fg="blue", bold=True)
    click.secho("=" * 60 + "\n", fg="blue", bold=True)

    click.secho("Welcome to ELESS! Here's how to get started:\n")

    click.secho("Step 1: Check System Health", fg="green", bold=True)
    click.secho("  Run: eless doctor")
    click.secho("  This checks if all dependencies are installed.\n")

    click.secho("Step 2: Configure ELESS", fg="green", bold=True)
    click.secho("  Run: eless init")
    click.secho("  This creates an optimal configuration for your system.\n")

    click.secho("Step 3: Process Documents", fg="green", bold=True)
    click.secho("  Run: eless process /path/to/your/documents")
    click.secho("  This processes your documents and creates embeddings.\n")

    click.secho("Step 4: Check Status", fg="green", bold=True)
    click.secho("  Run: eless status --all")
    click.secho("  This shows the processing status of all files.\n")

    click.secho("=" * 60, fg="blue", bold=True)
    click.secho("\n💡 Tips:", fg="yellow", bold=True)
    click.secho("  • Use --help with any command for more details")
    click.secho("  • Check docs at: docs/QUICK_START.md")
    click.secho("  • Run 'eless doctor' if you encounter issues\n")

    if click.confirm("Would you like to run the health check now?", default=True):
        click.echo()
        try:
            from eless.health_check import run_health_check

            run_health_check(verbose=True)
        except Exception as e:
            click.secho(f"Error: {e}", fg="red")


@cli.command()
def sysinfo():
    """
    Display system information and recommended settings.

    Shows detailed information about your system resources
    and the recommended ELESS configuration for optimal performance.

    Example:
        eless sysinfo
    """
    try:
        from eless.auto_config import print_system_info

        print_system_info()
    except Exception as e:
        click.secho(f"Error getting system info: {e}", fg="red")


@cli.command()
@click.option(
    "--export", type=click.Path(), help="Export demo files to specified directory"
)
def demo(export):
    """
    Run demo mode with sample documents.

    Creates sample documents and optionally processes them
    to demonstrate ELESS capabilities.

    Examples:
        eless demo                    # Interactive demo
        eless demo --export ./samples # Export demo files only
    """
    try:
        from eless.demo_data import run_demo_interactive, export_demo_files

        if export:
            export_demo_files(export)
        else:
            run_demo_interactive()
    except Exception as e:
        click.secho(f"Error running demo: {e}", fg="red")


@cli.command()
@click.option("--quick", is_flag=True, help="Run quick 5-minute tutorial")
def tutorial(quick):
    """
    Run interactive tutorial to learn ELESS.

    Step-by-step guide that teaches you how to use ELESS
    effectively with hands-on examples.

    Examples:
        eless tutorial         # Full tutorial (~15 min)
        eless tutorial --quick # Quick tutorial (~5 min)
    """
    try:
        from eless.tutorial_mode import run_tutorial, run_quick_tutorial

        if quick:
            run_quick_tutorial()
        else:
            run_tutorial()
    except Exception as e:
        click.secho(f"Error running tutorial: {e}", fg="red")


@cli.command()
@click.argument("action", type=click.Choice(["list", "show", "create"]))
@click.argument("template_name", required=False)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output path for created configuration file",
)
def template(action, template_name, output):
    """
    Manage configuration templates.

    Templates provide pre-configured settings for common scenarios:
    - minimal: Low resource usage (256MB RAM)
    - balanced: Auto-detected optimal settings
    - high-performance: Maximum performance (16GB+ RAM, GPU)
    - low-memory: Optimized for <2GB RAM
    - docker: Container-optimized

    Examples:
        eless template list                    # List all templates
        eless template show minimal            # Show template details
        eless template create minimal -o config.yaml  # Create config from template
    """
    try:
        from eless.config_templates import (
            list_templates,
            print_template_info,
            get_template,
        )
        import yaml

        if action == "list":
            click.secho("\n📝 Available Templates:", fg="blue", bold=True)
            click.secho("=" * 60, fg="blue")

            templates = list_templates()
            for name, description in templates.items():
                click.secho(f"\n  {name}", fg="green", bold=True)
                click.echo(f"    {description}")

            click.echo("\n" + "=" * 60)
            click.echo("\n💡 Use 'eless template show <name>' for details")
            click.echo("   Use 'eless template create <name>' to create config\n")

        elif action == "show":
            if not template_name:
                click.secho("Error: template name required", fg="red")
                return

            print_template_info(template_name)

        elif action == "create":
            if not template_name:
                click.secho("Error: template name required", fg="red")
                return

            config = get_template(template_name)

            # Determine output path
            if output:
                output_path = Path(output)
            else:
                output_path = Path.home() / ".eless" / f"{template_name}_config.yaml"
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(output_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

            click.secho(
                f"\n✓ Created configuration from '{template_name}' template:",
                fg="green",
            )
            click.secho(f"  {output_path}\n", fg="green", bold=True)

            click.echo("To use this configuration:")
            click.echo(f"  eless process /path/to/docs --config {output_path}")
            click.echo()

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
    except Exception as e:
        click.secho(f"Error managing templates: {e}", fg="red")


@cli.command()
@click.argument("source", type=click.Path(exists=True), required=True)
@click.option(
    "--database",
    "-db",
    default="chroma",
    help="Database to use (default: chroma)",
)
def go(source, database):
    """
    🚀 Quick process command - just works!

    Simplest way to process documents with sensible defaults.
    Automatically configures itself based on your system.

    This command:
      1. Auto-detects optimal settings
      2. Sets up the database
      3. Processes your documents
      4. Shows progress and results

    Examples:
        eless go documents/
        eless go myfile.pdf --database qdrant

    \b
    For more control, use: eless process <source> [OPTIONS]
    """
    try:
        from eless.auto_config import generate_auto_config
        from eless.eless_pipeline import ElessPipeline
        from eless.core.config_loader import ConfigLoader
        from eless.core.default_config import get_default_config

        click.secho("\n🚀 ELESS Quick Process", fg="blue", bold=True)
        click.secho("=" * 60, fg="blue")

        # Load base config
        base_config = get_default_config()

        # Auto-configure
        auto_settings = generate_auto_config()

        # Merge auto settings with base config
        base_config.update(auto_settings)

        # Set database
        base_config.setdefault("databases", {})
        base_config["databases"]["targets"] = [database]

        # Show what we're doing
        click.secho(f"\n📁 Source: {source}", fg="cyan")
        click.secho(f"💾 Database: {database}", fg="cyan")
        click.secho(
            f"⚙️  Batch size: {base_config['embedding']['batch_size']}", fg="cyan"
        )
        click.secho(f"🖥️  Device: {base_config['embedding']['device']}", fg="cyan")
        click.secho()

        # Create and run pipeline
        click.secho("Processing...", fg="yellow")
        pipeline = ElessPipeline(base_config)
        pipeline.run_process(source)

        # Show results
        click.secho("\n✓ Processing complete!", fg="green", bold=True)

        # Show status
        files = pipeline.state_manager.get_all_files()
        loaded = [f for f in files if f["status"] == "LOADED"]
        errors = [f for f in files if f["status"] == "ERROR"]

        click.secho(f"\n📊 Results:", fg="blue", bold=True)
        click.secho(f"  Processed: {len(loaded)} files")
        if errors:
            click.secho(f"  Errors: {len(errors)} files", fg="yellow")

        click.secho(f"\n💡 Next steps:", fg="cyan")
        click.secho(f"  View status: eless status --all")
        click.secho(f"  Check logs: ls .eless_logs/")
        click.secho()

    except KeyboardInterrupt:
        click.secho("\n\n⚠️  Processing interrupted", fg="yellow")
        click.secho(
            "💡 Resume with: eless process {} --resume\n".format(source), fg="cyan"
        )
    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg="red")
        click.secho("💡 Run 'eless doctor' to diagnose issues\n", fg="cyan")


if __name__ == "__main__":
    cli()
