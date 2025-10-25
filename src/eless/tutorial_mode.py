"""
Tutorial mode for ELESS.
Provides step-by-step guided learning experience.
"""

import click
import time
from pathlib import Path
from typing import Optional


def print_header(text: str):
    """Print a formatted header."""
    click.secho("\n" + "=" * 60, fg="blue", bold=True)
    click.secho(f"  {text}", fg="blue", bold=True)
    click.secho("=" * 60, fg="blue")


def print_step(step_num: int, total: int, title: str):
    """Print a step header."""
    click.secho(f"\n📍 Step {step_num}/{total}: {title}", fg="green", bold=True)
    click.secho("-" * 60, fg="green")


def wait_for_user(prompt: str = "Press Enter to continue..."):
    """Wait for user to press Enter."""
    click.echo()
    click.pause(prompt)


def run_tutorial():
    """
    Run the complete ELESS tutorial.
    """
    print_header("🎓 ELESS Tutorial - Learn by Doing")

    click.echo("\nWelcome to the ELESS tutorial!")
    click.echo("This interactive guide will teach you how to use ELESS effectively.")
    click.echo("\nEstimated time: 10-15 minutes")
    click.echo()

    if not click.confirm("Ready to start?", default=True):
        click.secho("\nTutorial cancelled. Come back anytime!", fg="yellow")
        return

    # Step 1: Understanding ELESS
    print_step(1, 7, "Understanding ELESS")
    click.echo("\nELESS (Evolving Low-resource Embedding and Storage System)")
    click.echo("is a tool that helps you:")
    click.echo()
    click.echo("  • Process documents into searchable embeddings")
    click.echo("  • Store them in vector databases")
    click.echo("  • Build RAG (Retrieval Augmented Generation) systems")
    click.echo("  • Work efficiently even on low-resource systems")
    click.echo()
    click.secho(
        "💡 Think of ELESS as a smart librarian that reads your documents", fg="cyan"
    )
    click.secho(
        "   and remembers them in a way that makes finding information easy.", fg="cyan"
    )

    wait_for_user()

    # Step 2: System Check
    print_step(2, 7, "Checking Your System")
    click.echo("\nLet's check if your system is ready to use ELESS.")
    click.echo("We'll run the 'doctor' command to diagnose your setup.")
    click.echo()

    if click.confirm("Run system health check?", default=True):
        try:
            from eless.health_check import run_health_check

            click.echo()
            run_health_check(verbose=False)
        except Exception as e:
            click.secho(f"\n⚠️  Health check error: {e}", fg="yellow")

    wait_for_user()

    # Step 3: Configuration
    print_step(3, 7, "Setting Up Configuration")
    click.echo("\nELESS needs to know about your system to work optimally.")
    click.echo("The 'init' command creates a configuration file automatically.")
    click.echo()
    click.secho("💡 Configuration tells ELESS:", fg="cyan")
    click.echo("   • How much memory to use")
    click.echo("   • How many files to process at once")
    click.echo("   • Which database to use")
    click.echo()

    if click.confirm("Create configuration now?", default=True):
        try:
            from eless.auto_config import generate_auto_config, print_system_info

            click.echo()
            print_system_info()

            config = generate_auto_config()

            # Save config
            config_dir = Path.home() / ".eless"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "tutorial_config.yaml"

            import yaml

            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

            click.secho(f"\n✓ Configuration saved to: {config_path}", fg="green")
        except Exception as e:
            click.secho(f"\n⚠️  Configuration error: {e}", fg="yellow")

    wait_for_user()

    # Step 4: Understanding the Pipeline
    print_step(4, 7, "Understanding the Processing Pipeline")
    click.echo("\nELESS processes documents in several stages:")
    click.echo()
    click.secho("  1️⃣  Scanning", fg="yellow", bold=True)
    click.echo("     Finds all documents in your directory")
    click.echo()
    click.secho("  2️⃣  Chunking", fg="yellow", bold=True)
    click.echo("     Splits documents into smaller pieces")
    click.echo()
    click.secho("  3️⃣  Embedding", fg="yellow", bold=True)
    click.echo("     Converts text into numerical vectors")
    click.echo()
    click.secho("  4️⃣  Loading", fg="yellow", bold=True)
    click.echo("     Stores vectors in the database")
    click.echo()
    click.secho(
        "💡 Each stage is resumable - if interrupted, ELESS picks up", fg="cyan"
    )
    click.secho("   where it left off!", fg="cyan")

    wait_for_user()

    # Step 5: Demo Data
    print_step(5, 7, "Creating Demo Data")
    click.echo("\nLet's create some sample documents to practice with.")
    click.echo()

    if click.confirm("Create demo documents?", default=True):
        try:
            from eless.demo_data import create_demo_dataset

            demo_dir = Path.cwd() / "eless_tutorial_demo"
            demo_dir = create_demo_dataset(demo_dir)

            click.secho(f"\n✓ Created demo files in: {demo_dir}", fg="green")
            click.echo("\nDemo files include:")
            click.echo("  • Introduction to ELESS")
            click.echo("  • Getting started guide")
            click.echo("  • Architecture overview")
            click.echo("  • Machine learning concepts")
            click.echo("  • Data science fundamentals")

            tutorial_demo_dir = demo_dir
        except Exception as e:
            click.secho(f"\n⚠️  Demo creation error: {e}", fg="yellow")
            tutorial_demo_dir = None
    else:
        tutorial_demo_dir = None

    wait_for_user()

    # Step 6: Processing Documents
    print_step(6, 7, "Processing Your First Documents")
    click.echo("\nNow let's process the demo documents!")
    click.echo()
    click.secho(
        "💡 The 'go' command is the simplest way to process documents.", fg="cyan"
    )
    click.secho("   It automatically configures everything for you.", fg="cyan")
    click.echo()

    if tutorial_demo_dir and click.confirm("Process demo documents now?", default=True):
        try:
            from eless.auto_config import generate_auto_config
            from eless.core.default_config import get_default_config
            from eless.core.logging_config import setup_logging
            from eless.eless_pipeline import ElessPipeline

            click.echo("\n🚀 Starting processing...\n")

            # Create config
            config = get_default_config()
            auto_config = generate_auto_config()
            config.update(auto_config)
            config["databases"] = {"targets": ["chroma"]}

            # Setup logging
            setup_logging(config)

            # Process
            pipeline = ElessPipeline(config)
            pipeline.run_process(str(tutorial_demo_dir))

            click.secho("\n✓ Processing complete!", fg="green", bold=True)

            # Show results
            files = pipeline.state_manager.get_all_files()
            loaded = [f for f in files if f.get("status") == "LOADED"]

            click.echo(f"\n📊 Processed {len(loaded)} files successfully!")

        except Exception as e:
            click.secho(f"\n⚠️  Processing error: {e}", fg="yellow")
    elif not tutorial_demo_dir:
        click.echo("Skipping processing (no demo data available)")

    wait_for_user()

    # Step 7: Next Steps
    print_step(7, 7, "Next Steps and Resources")
    click.echo("\nCongratulations! You've completed the ELESS tutorial! 🎉")
    click.echo()
    click.secho("What you learned:", fg="green", bold=True)
    click.echo("  ✓ What ELESS does and why it's useful")
    click.echo("  ✓ How to check system health with 'doctor'")
    click.echo("  ✓ How to configure ELESS with 'init'")
    click.echo("  ✓ The document processing pipeline")
    click.echo("  ✓ How to process documents with 'go'")
    click.echo()

    click.secho("Useful Commands:", fg="blue", bold=True)
    click.echo("  eless doctor              Check system health")
    click.echo("  eless init                Set up configuration")
    click.echo("  eless go <directory>      Quick process documents")
    click.echo("  eless process <directory> Process with full options")
    click.echo("  eless status --all        Check processing status")
    click.echo("  eless monitor             Real-time system monitoring")
    click.echo("  eless --help              Show all commands")
    click.echo()

    click.secho("Resources:", fg="blue", bold=True)
    click.echo("  📖 Documentation: docs/")
    click.echo("  💻 GitHub: https://github.com/Bandalaro/eless")
    click.echo("  📝 Examples: examples/")
    click.echo()

    click.secho("💡 Try processing your own documents:", fg="cyan")
    click.echo("   eless go /path/to/your/documents")
    click.echo()

    print_header("✨ Tutorial Complete!")
    click.echo()


def run_quick_tutorial():
    """
    Run a quick 5-minute tutorial focusing on essential commands.
    """
    print_header("⚡ ELESS Quick Tutorial (5 min)")

    click.echo("\nThis is a condensed version of the full tutorial.")
    click.echo("You'll learn the essential commands in 5 minutes.")
    click.echo()

    if not click.confirm("Ready?", default=True):
        return

    # Quick system check
    click.secho("\n1️⃣  System Check", fg="green", bold=True)
    click.echo("   Command: eless doctor")
    click.echo("   Purpose: Verify ELESS is installed correctly")
    wait_for_user("Press Enter to see example...")

    # Quick init
    click.secho("\n2️⃣  Configuration", fg="green", bold=True)
    click.echo("   Command: eless init")
    click.echo("   Purpose: Create optimal configuration for your system")
    wait_for_user("Press Enter to continue...")

    # Quick process
    click.secho("\n3️⃣  Process Documents", fg="green", bold=True)
    click.echo("   Command: eless go /path/to/documents")
    click.echo("   Purpose: Process all documents in a directory")
    click.echo()
    click.secho("   💡 That's it! The 'go' command does everything:", fg="cyan")
    click.echo("      • Auto-configures settings")
    click.echo("      • Processes all files")
    click.echo("      • Shows progress")
    click.echo("      • Handles errors gracefully")
    wait_for_user("Press Enter to continue...")

    # Status check
    click.secho("\n4️⃣  Check Status", fg="green", bold=True)
    click.echo("   Command: eless status --all")
    click.echo("   Purpose: See what's been processed")
    wait_for_user("Press Enter to finish...")

    click.secho("\n✨ Quick Tutorial Complete!", fg="green", bold=True)
    click.echo()
    click.echo("Now try: eless go <your-directory>")
    click.echo()
