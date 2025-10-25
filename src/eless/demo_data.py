"""
Demo dataset functionality for ELESS.
Provides sample documents for testing and learning.
"""

import click
import tempfile
import shutil
from pathlib import Path
from typing import Optional


SAMPLE_DOCUMENTS = {
    "sample1.txt": """
ELESS: Evolving Low-resource Embedding and Storage System

ELESS is a powerful yet resource-efficient RAG (Retrieval Augmented Generation) 
data processing pipeline designed to work on systems with limited resources.

Key Features:
- Multi-database support (ChromaDB, FAISS, Qdrant, PostgreSQL, Cassandra)
- Automatic resource detection and configuration
- Intelligent caching with LRU eviction
- Adaptive batch sizing based on available memory
- Comprehensive state management with resumption support
- Flexible chunking strategies for optimal text processing

ELESS makes it easy to build semantic search and RAG applications without 
requiring expensive hardware or cloud infrastructure.
""",
    "sample2.txt": """
Getting Started with ELESS

Installation:
pip install eless

Quick Start:
1. Check system health: eless doctor
2. Configure: eless init
3. Process documents: eless process /path/to/docs
4. Monitor progress: eless monitor

ELESS automatically configures itself based on your system's available resources,
making it perfect for both development laptops and production servers.

For more information, visit: https://github.com/Bandalaro/eless
""",
    "sample3.txt": """
ELESS Architecture Overview

The ELESS pipeline consists of several key components:

1. File Scanner
   - Discovers and catalogs input files
   - Generates content hashes for deduplication
   - Supports multiple file formats (PDF, DOCX, TXT, etc.)

2. Chunker
   - Splits documents into processable chunks
   - Configurable chunk size and overlap
   - Multiple chunking strategies available

3. Embedder
   - Generates vector embeddings using Sentence Transformers
   - Supports batch processing for efficiency
   - Adaptive batching based on memory pressure

4. Database Loader
   - Loads embeddings into vector databases
   - Multi-database support for redundancy
   - Batch operations for optimal performance

5. State Manager
   - Tracks processing state for each file
   - Enables resumption after interruptions
   - Persistent state storage

The modular architecture makes ELESS easy to extend and customize for
specific use cases.
""",
    "machine_learning.md": """
# Machine Learning Concepts

## What is Machine Learning?

Machine learning is a subset of artificial intelligence that enables 
systems to learn and improve from experience without being explicitly 
programmed.

## Types of Machine Learning

### Supervised Learning
- Classification: Categorizing data into predefined classes
- Regression: Predicting continuous values

### Unsupervised Learning
- Clustering: Grouping similar data points
- Dimensionality Reduction: Reducing feature space

### Reinforcement Learning
- Agent-based learning through rewards and penalties
- Used in robotics, game AI, and autonomous systems

## Applications
- Natural Language Processing
- Computer Vision
- Recommendation Systems
- Fraud Detection
- Medical Diagnosis
""",
    "data_science.md": """
# Data Science Fundamentals

## The Data Science Process

1. **Problem Definition**
   - Understand business objectives
   - Define success metrics

2. **Data Collection**
   - Gather relevant data
   - Ensure data quality

3. **Data Cleaning**
   - Handle missing values
   - Remove duplicates
   - Fix inconsistencies

4. **Exploratory Analysis**
   - Visualize data distributions
   - Identify patterns and correlations
   - Generate hypotheses

5. **Feature Engineering**
   - Create meaningful features
   - Transform variables
   - Select important features

6. **Model Building**
   - Choose appropriate algorithms
   - Train and validate models
   - Tune hyperparameters

7. **Deployment**
   - Put models into production
   - Monitor performance
   - Iterate and improve
""",
}


def create_demo_dataset(output_dir: Optional[Path] = None) -> Path:
    """
    Create a demo dataset for testing ELESS.

    Args:
        output_dir: Directory to create demo files in (uses temp dir if None)

    Returns:
        Path to the demo dataset directory
    """
    if output_dir is None:
        # Create a temporary directory
        output_dir = Path(tempfile.mkdtemp(prefix="eless_demo_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample documents
    for filename, content in SAMPLE_DOCUMENTS.items():
        file_path = output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())

    return output_dir


def run_demo_interactive():
    """
    Run an interactive demo that creates sample data and processes it.
    """
    click.secho("\n" + "=" * 60, fg="cyan", bold=True)
    click.secho("  🎨 ELESS Demo Mode", fg="cyan", bold=True)
    click.secho("=" * 60 + "\n", fg="cyan", bold=True)

    click.echo("This demo will:")
    click.echo("  1. Create sample documents")
    click.echo("  2. Process them with ELESS")
    click.echo("  3. Show you the results")
    click.echo()

    if not click.confirm("Continue with demo?", default=True):
        click.secho("\nDemo cancelled.", fg="yellow")
        return

    # Ask where to create demo files
    use_temp = click.confirm(
        "\nCreate demo files in a temporary directory?", default=True
    )

    if use_temp:
        demo_dir = create_demo_dataset()
        click.secho(f"\n✓ Created demo files in: {demo_dir}", fg="green")
        cleanup_after = click.confirm(
            "\nClean up demo files after processing?", default=True
        )
    else:
        default_dir = Path.cwd() / "eless_demo"
        demo_path = click.prompt(
            "\nEnter directory for demo files", default=str(default_dir), type=str
        )
        demo_dir = Path(demo_path)
        demo_dir.mkdir(parents=True, exist_ok=True)
        demo_dir = create_demo_dataset(demo_dir)
        click.secho(f"\n✓ Created demo files in: {demo_dir}", fg="green")
        cleanup_after = False

    # Show what was created
    click.secho("\n📄 Demo Files:", fg="blue", bold=True)
    for filename in SAMPLE_DOCUMENTS.keys():
        file_path = demo_dir / filename
        size = file_path.stat().st_size
        click.echo(f"  {filename:30} ({size:,} bytes)")

    click.echo()

    # Ask if they want to process now
    if click.confirm("Process demo files now?", default=True):
        click.secho("\n🚀 Processing demo files...\n", fg="yellow")

        # Import and run processing
        try:
            from eless.auto_config import generate_auto_config
            from eless.core.config_loader import ConfigLoader
            from eless.core.default_config import get_default_config
            from eless.core.logging_config import setup_logging
            from eless.eless_pipeline import ElessPipeline
            import logging

            # Create a simple config
            config = get_default_config()
            auto_config = generate_auto_config()
            config.update(auto_config)
            config["databases"] = {"targets": ["chroma"]}

            # Setup logging
            setup_logging(config)
            logger = logging.getLogger("ELESS.Demo")

            # Create pipeline and process
            click.echo("Initializing ELESS pipeline...")
            pipeline = ElessPipeline(config)

            click.echo(f"Processing documents from {demo_dir}...")
            pipeline.run_process(str(demo_dir))

            click.secho("\n✓ Demo processing complete!", fg="green", bold=True)

            # Show results
            state_manager = pipeline.state_manager
            files = state_manager.get_all_files()

            click.secho("\n📊 Results:", fg="blue", bold=True)
            click.echo(f"  Total files: {len(files)}")

            loaded = [f for f in files if f.get("status") == "LOADED"]
            errors = [f for f in files if f.get("status") == "ERROR"]

            click.secho(f"  Successfully processed: {len(loaded)}", fg="green")
            if errors:
                click.secho(f"  Errors: {len(errors)}", fg="red")

        except Exception as e:
            click.secho(f"\n❌ Error during demo: {e}", fg="red")
            logger.error(f"Demo processing error: {e}", exc_info=True)
    else:
        click.secho(f"\n💡 To process later, run:", fg="cyan")
        click.secho(f"   eless process {demo_dir}\n")

    # Cleanup
    if cleanup_after:
        try:
            shutil.rmtree(demo_dir)
            click.secho(f"\n✓ Cleaned up demo files", fg="green")
        except Exception as e:
            click.secho(f"\n⚠️  Could not clean up {demo_dir}: {e}", fg="yellow")

    click.secho("\n" + "=" * 60, fg="cyan")
    click.secho("Demo complete! 🎉", fg="cyan", bold=True)
    click.secho("=" * 60 + "\n", fg="cyan")


def export_demo_files(output_dir: str):
    """
    Export demo files to a specified directory.

    Args:
        output_dir: Directory to export files to
    """
    output_path = Path(output_dir)
    demo_dir = create_demo_dataset(output_path)

    click.secho(f"\n✓ Exported {len(SAMPLE_DOCUMENTS)} demo files to:", fg="green")
    click.secho(f"  {demo_dir}\n", fg="green", bold=True)

    click.echo("Files created:")
    for filename in SAMPLE_DOCUMENTS.keys():
        click.echo(f"  • {filename}")

    click.echo()
