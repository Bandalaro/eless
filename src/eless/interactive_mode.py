"""
Interactive CLI mode for ELESS.
Provides guided prompts for processing documents.
"""

import click
from pathlib import Path
from typing import Optional, Dict, Any


def prompt_for_directory() -> Optional[str]:
    """
    Prompt user to select a directory to process.

    Returns:
        Directory path or None if cancelled
    """
    click.secho("\n📁 Select Directory to Process", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    while True:
        directory = click.prompt(
            "\nEnter the path to your documents directory", type=str, default="."
        )

        dir_path = Path(directory).expanduser().resolve()

        if not dir_path.exists():
            click.secho(f"✗ Directory not found: {dir_path}", fg="red")
            if not click.confirm("Try again?", default=True):
                return None
            continue

        if not dir_path.is_dir():
            click.secho(f"✗ Not a directory: {dir_path}", fg="red")
            if not click.confirm("Try again?", default=True):
                return None
            continue

        # Count potential files
        file_count = len([f for f in dir_path.rglob("*") if f.is_file()])

        click.secho(f"\n✓ Found directory with {file_count} files", fg="green")

        if click.confirm(f"Process '{dir_path}'?", default=True):
            return str(dir_path)

        if not click.confirm("Select a different directory?", default=True):
            return None


def prompt_for_database() -> str:
    """
    Prompt user to select a database.

    Returns:
        Database name (chroma, qdrant, faiss, etc.)
    """
    click.secho("\n💾 Select Vector Database", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    click.echo("\nAvailable databases:")
    click.echo("  1. ChromaDB   - Easy setup, local storage (Recommended)")
    click.echo("  2. FAISS      - Fast similarity search, local")
    click.echo("  3. Qdrant     - Cloud-ready, scalable")
    click.echo("  4. PostgreSQL - Traditional SQL with vectors")
    click.echo("  5. Cassandra  - Distributed NoSQL")

    database_map = {
        "1": "chroma",
        "2": "faiss",
        "3": "qdrant",
        "4": "postgresql",
        "5": "cassandra",
    }

    choice = click.prompt(
        "\nChoose database", type=click.Choice(["1", "2", "3", "4", "5"]), default="1"
    )

    selected = database_map[choice]
    click.secho(f"✓ Selected: {selected}", fg="green")

    return selected


def prompt_for_chunk_size() -> int:
    """
    Prompt user to select chunk size.

    Returns:
        Chunk size in characters
    """
    click.secho("\n✂️  Select Chunk Size", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    click.echo("\nChunk size determines how text is split:")
    click.echo("  1. Auto-detect  - System determines optimal size (Recommended)")
    click.echo("  2. Small (256)  - Good for precise matching")
    click.echo("  3. Medium (512) - Balanced approach")
    click.echo("  4. Large (1024) - More context per chunk")

    chunk_map = {
        "1": 0,  # 0 means auto
        "2": 256,
        "3": 512,
        "4": 1024,
    }

    choice = click.prompt(
        "\nChoose chunk size", type=click.Choice(["1", "2", "3", "4"]), default="1"
    )

    size = chunk_map[choice]

    if size == 0:
        click.secho("✓ Will auto-detect optimal chunk size", fg="green")
    else:
        click.secho(f"✓ Selected: {size} characters", fg="green")

    return size


def prompt_for_batch_size() -> int:
    """
    Prompt user to select batch size.

    Returns:
        Batch size for embedding generation
    """
    click.secho("\n⚙️  Select Batch Size", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    click.echo("\nBatch size affects memory usage and speed:")
    click.echo("  1. Auto-detect  - System determines optimal size (Recommended)")
    click.echo("  2. Small (8)    - Low memory usage")
    click.echo("  3. Medium (32)  - Balanced")
    click.echo("  4. Large (64)   - Fast but needs more memory")

    batch_map = {
        "1": 0,  # 0 means auto
        "2": 8,
        "3": 32,
        "4": 64,
    }

    choice = click.prompt(
        "\nChoose batch size", type=click.Choice(["1", "2", "3", "4"]), default="1"
    )

    size = batch_map[choice]

    if size == 0:
        click.secho("✓ Will auto-detect optimal batch size", fg="green")
    else:
        click.secho(f"✓ Selected: {size}", fg="green")

    return size


def prompt_for_resume() -> bool:
    """
    Ask if user wants to resume from previous processing.

    Returns:
        True if resume is desired
    """
    click.secho("\n🔄 Resume Options", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    return click.confirm("\nResume from last checkpoint (if available)?", default=True)


def run_interactive_process() -> Optional[Dict[str, Any]]:
    """
    Run interactive mode to gather processing options.

    Returns:
        Dictionary of processing options or None if cancelled
    """
    click.secho("\n" + "=" * 60, fg="cyan", bold=True)
    click.secho("  🎯 ELESS Interactive Mode", fg="cyan", bold=True)
    click.secho("=" * 60 + "\n", fg="cyan", bold=True)

    click.echo("This wizard will help you configure document processing.\n")

    # Step 1: Directory selection
    directory = prompt_for_directory()
    if not directory:
        click.secho("\n⚠️  Processing cancelled", fg="yellow")
        return None

    # Step 2: Database selection
    database = prompt_for_database()

    # Step 3: Advanced options
    click.secho("\n⚙️  Advanced Options", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    show_advanced = click.confirm("\nConfigure advanced options?", default=False)

    chunk_size = None
    batch_size = None
    resume = True

    if show_advanced:
        chunk_size = prompt_for_chunk_size()
        if chunk_size == 0:
            chunk_size = None

        batch_size = prompt_for_batch_size()
        if batch_size == 0:
            batch_size = None

        resume = prompt_for_resume()

    # Summary
    click.secho("\n📋 Configuration Summary", fg="green", bold=True)
    click.secho("=" * 60, fg="green")
    click.secho(f"  Directory: {directory}")
    click.secho(f"  Database: {database}")
    click.secho(f"  Chunk size: {chunk_size or 'Auto'}")
    click.secho(f"  Batch size: {batch_size or 'Auto'}")
    click.secho(f"  Resume: {resume}")
    click.secho()

    if not click.confirm("Start processing?", default=True):
        click.secho("\n⚠️  Processing cancelled", fg="yellow")
        return None

    return {
        "source": directory,
        "database": database,
        "chunk_size": chunk_size,
        "batch_size": batch_size,
        "resume": resume,
    }


def prompt_for_config_template() -> str:
    """
    Prompt user to select a configuration template.

    Returns:
        Template name
    """
    click.secho("\n📝 Select Configuration Template", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")

    click.echo("\nAvailable templates:")
    click.echo("  1. Minimal         - Low resource usage (256MB RAM)")
    click.echo("  2. Balanced        - Auto-detected optimal settings")
    click.echo("  3. High-Performance - Maximum performance")
    click.echo("  4. Low-Memory      - Optimized for <2GB RAM systems")
    click.echo("  5. Docker          - Container-optimized")

    template_map = {
        "1": "minimal",
        "2": "balanced",
        "3": "high-performance",
        "4": "low-memory",
        "5": "docker",
    }

    choice = click.prompt(
        "\nChoose template", type=click.Choice(["1", "2", "3", "4", "5"]), default="2"
    )

    selected = template_map[choice]
    click.secho(f"✓ Selected: {selected}", fg="green")

    return selected
