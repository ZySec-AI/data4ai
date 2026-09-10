"""CLI commands for Data4AI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from data4ai.config import settings
from data4ai.document_handler import DocumentHandler
from data4ai.error_handler import check_environment_variables, error_handler
from data4ai.publisher import HuggingFacePublisher
from data4ai.utils import setup_logging

app = typer.Typer(
    name="data4ai",
    help="Data4AI - AI-powered dataset generation for instruction tuning",
    add_completion=False,
)
console = Console()

# Import DatasetGenerator for test compatibility
try:
    from .generator import DatasetGenerator
except ImportError:
    DatasetGenerator = None  # For testing


def _version_callback(value: bool):
    if value:
        from data4ai import __version__
        from data4ai.version_checker import VersionChecker

        console.print(f"data4ai {__version__}")

        # Check for updates
        checker = VersionChecker()
        has_update, current_ver, latest_ver = checker.check_for_updates()

        if has_update and latest_ver:
            console.print(
                checker.format_update_message(current_ver, latest_ver), style="yellow"
            )
        elif latest_ver:
            console.print("✅ You're using the latest version!", style="green")

        raise typer.Exit()


def _check_for_updates_background():
    """Check for updates in background (non-blocking)."""
    try:
        from data4ai.version_checker import VersionChecker

        checker = VersionChecker()

        # Only check if cache is stale or missing
        cache_data = checker._load_cache()
        if cache_data:
            return  # Skip if we have recent cache

        # Quick check for updates
        has_update, current_ver, latest_ver = checker.check_for_updates()

        if has_update and latest_ver:
            # Show a brief, non-intrusive message
            console.print(
                f"\n💡 Data4AI v{latest_ver} is available! "
                f"(current: v{current_ver})\n"
                f"   Run: pip install --upgrade data4ai\n",
                style="dim yellow",
            )
    except Exception:
        # Silently fail - don't interrupt user workflow
        pass


@app.callback()
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    no_update_check: bool = typer.Option(
        False,
        "--no-update-check",
        help="Skip checking for updates",
        envvar="DATA4AI_NO_UPDATE_CHECK",
    ),
):
    """Data4AI - Generate high-quality datasets for LLM training."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")

    # Periodic update check (non-blocking)
    if not no_update_check:
        _check_for_updates_background()


@app.command()
@error_handler
def push(
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Dataset directory and repo name"
    ),
    private: bool = typer.Option(False, "--private", help="Make dataset private"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Dataset description"
    ),
    token: Optional[str] = typer.Option(None, "--token", help="HuggingFace token"),
):
    """Upload dataset to HuggingFace Hub."""
    console.print("Pushing dataset to HuggingFace...", style="blue")

    # Initialize publisher
    hf_token = token or settings.hf_token
    publisher = HuggingFacePublisher(token=hf_token)

    # Push dataset
    dataset_dir = Path("outputs/datasets") / repo
    with console.status("Uploading files..."):
        url = publisher.push_dataset(
            dataset_dir=dataset_dir,
            repo_name=repo,
            private=private,
            description=description,
        )

    console.print("✅ Dataset uploaded successfully!", style="green")
    console.print(f"🔗 View at: {url}", style="cyan")


@app.command("doc")
@error_handler
def doc_to_dataset(
    input_path: Path = typer.Argument(
        ..., help="Input document or folder (preserves folder structure in output)"
    ),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("chatml", "--dataset", "-d", help="Dataset schema"),
    extraction_type: str = typer.Option(
        "qa",
        "--type",
        "-t",
        help="Extraction type: qa, summary, instruction",
    ),
    count: int = typer.Option(100, "--count", "-c", help="Number of examples"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Examples per batch"),
    chunk_size: int = typer.Option(
        1000, "--chunk-size", help="Document chunk size in characters (default: 1000)"
    ),
    chunk_tokens: Optional[int] = typer.Option(
        None, "--chunk-tokens", help="Chunk size in tokens (overrides --chunk-size)"
    ),
    chunk_overlap: int = typer.Option(
        200, "--chunk-overlap", help="Overlap between chunks in chars/tokens"
    ),
    taxonomy: Optional[str] = typer.Option(
        None,
        "--taxonomy",
        help="Enable Bloom's taxonomy: 'balanced', 'basic', or 'advanced'",
    ),
    include_provenance: bool = typer.Option(
        False, "--provenance", help="Include source references in dataset"
    ),
    all_levels: bool = typer.Option(
        True,
        "--all-levels/--no-all-levels",
        help="QA: ensure all Bloom levels per document (>=6 examples)",
    ),
    verify_quality: bool = typer.Option(
        False, "--verify", help="Enable quality verification pass (increases API calls)"
    ),
    long_context: bool = typer.Option(
        False, "--long-context", help="Merge chunks for long-context models"
    ),
    dedup_strategy: str = typer.Option(
        "content",
        "--dedup-strategy",
        help="Dedup strategy: exact, fuzzy, instruction, content",
    ),
    dedup_threshold: float = typer.Option(
        0.97,
        "--dedup-threshold",
        help="Fuzzy/content dedup similarity threshold (0-1)",
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", help="Scan folders recursively"
    ),
    file_types: Optional[str] = typer.Option(
        None, "--file-types", help="Comma-separated file types (pdf,docx,md,txt)"
    ),
    advanced: bool = typer.Option(
        False, "--advanced", help="Use advanced extraction (slower but better)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate generation"),
    huggingface: bool = typer.Option(
        False, "--huggingface", "-hf", help="Push to HuggingFace"
    ),
):
    """Generate dataset from document(s) - supports files and folders.

    Automatically preserves folder structure while creating a combined dataset."""

    # Check if input is file or folder
    if input_path.is_dir():
        console.print(f"📁 Scanning folder: {input_path}", style="blue")

        # Parse file types if provided
        types_to_scan = None
        if file_types:
            types_to_scan = [ft.strip() for ft in file_types.split(",")]

        # Scan folder for documents
        try:
            documents = DocumentHandler.scan_folder(
                input_path, recursive=recursive, file_types=types_to_scan
            )
            if not documents:
                console.print("❌ No supported documents found in folder", style="red")
                raise typer.Exit(1)

            console.print(f"📚 Found {len(documents)} documents:", style="cyan")
            for doc in documents[:10]:  # Show first 10
                console.print(f"  • {doc.name}", style="dim")
            if len(documents) > 10:
                console.print(f"  ... and {len(documents) - 10} more", style="dim")

        except Exception as e:
            console.print(f"❌ {str(e)}", style="red")
            raise typer.Exit(1) from e
    else:
        console.print(f"📄 Processing document: {input_path.name}", style="blue")

        # Validate document type
        try:
            doc_type = DocumentHandler.detect_document_type(input_path)
            console.print(f"📋 Document type: {doc_type.upper()}", style="cyan")
        except Exception as e:
            console.print(f"❌ {str(e)}", style="red")
            raise typer.Exit(1) from e

    # Show info about quality options if not using them
    if not any(
        [taxonomy, include_provenance, verify_quality, long_context, chunk_tokens]
    ):
        console.print(
            "💡 Tip: Use --taxonomy, --provenance, or --verify for higher quality datasets",
            style="dim",
        )

    # Handle dry run without initializing generator
    if dry_run:
        console.print("🔍 Dry run mode - simulating generation", style="yellow")
        console.print(f"📄 Would process: {input_path}", style="cyan")
        console.print(f"📊 Would generate: {count} {dataset} examples", style="cyan")
        console.print(
            f"📁 Would save to: {Path('outputs/datasets') / repo}", style="cyan"
        )

        if input_path.is_dir() and "documents" in locals():
            console.print(
                f"📚 Found {len(documents)} documents to process", style="cyan"
            )

        console.print("✅ Dry run completed", style="green")
        return

    # Lazy import to avoid heavy dependencies at CLI import time
    from data4ai.generator import DatasetGenerator

    # Initialize generator with quality options (only for actual generation)
    generator = DatasetGenerator()

    # Generate dataset
    output_path = Path("outputs/datasets") / repo

    status_msg = "Generating dataset from document(s)..."
    if input_path.is_dir():
        status_msg = f"Generating dataset from {len(documents) if 'documents' in locals() else 'multiple'} documents..."

    # Add quality indicators to status
    if any([taxonomy, verify_quality, long_context]):
        quality_features = []
        if taxonomy:
            quality_features.append("taxonomy")
        if verify_quality:
            quality_features.append("verification")
        if long_context:
            quality_features.append("long-context")
        status_msg += f" [Quality: {', '.join(quality_features)}]"

    with console.status(status_msg):
        result = generator.generate_from_document_sync(
            document_path=input_path,
            output_dir=output_path,
            schema_name=dataset,
            extraction_type=extraction_type,
            count=count,
            batch_size=batch_size,
            chunk_size=chunk_size,
            chunk_tokens=chunk_tokens,
            chunk_overlap=chunk_overlap,
            taxonomy=taxonomy,
            include_provenance=include_provenance,
            taxonomy_all_levels=all_levels,
            verify_quality=verify_quality,
            long_context=long_context,
            use_advanced=advanced,
            recursive=recursive,
            dry_run=False,  # Already handled above
            dedup_strategy=dedup_strategy,
            dedup_threshold=dedup_threshold,
        )

        # Process results (dry_run already handled above)
        console.print(f"✅ Generated {result['row_count']} examples", style="green")
        console.print(f"💾 Saved to: {result['output_path']}", style="green")

        # Show document stats
        if result.get("total_documents", 1) > 1:
            console.print(
                f"📊 Processed {result['chunks_processed']} chunks from {result['total_documents']} documents",
                style="cyan",
            )
        else:
            console.print(
                f"📊 Processed {result['chunks_processed']} document chunks",
                style="cyan",
            )

        # Push to HuggingFace if requested
        if huggingface:
            hf_token = settings.hf_token
            if not hf_token:
                console.print(
                    "⚠️  HF_TOKEN not set. Skipping HuggingFace upload.", style="yellow"
                )
            else:
                doc_desc = (
                    f"{result.get('total_documents', 1)} documents"
                    if result.get("total_documents", 1) > 1
                    else "document"
                )
                with console.status("Pushing to HuggingFace Hub..."):
                    publisher = HuggingFacePublisher(
                        token=hf_token, organization=settings.hf_organization
                    )
                    hf_url = publisher.push_dataset(
                        dataset_dir=output_path,
                        repo_name=repo,
                        description=f"Dataset generated from {doc_desc} using {extraction_type} extraction",
                    )
                console.print(f"🤗 Published to: {hf_url}", style="green")


@app.command()
@error_handler
def prompt(
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Natural language description of dataset to generate",
    ),
    count: int = typer.Option(
        100, "--count", "-c", help="Number of examples to generate"
    ),
    dataset: str = typer.Option(
        "chatml", "--dataset", help="Dataset schema (chatml, alpaca)"
    ),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Examples per batch"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be generated without creating files"
    ),
    use_dspy: bool = typer.Option(
        True, "--use-dspy/--no-use-dspy", help="Use DSPy for prompt optimization"
    ),
    dspy_model: Optional[str] = typer.Option(
        None, "--dspy-model", help="DSPy model for prompt optimization"
    ),
):
    """Generate dataset from natural language description."""

    if dry_run:
        console.print("🧪 [bold cyan]Dry Run Mode[/bold cyan]")
        console.print(f"Repository: {repo}")
        console.print(f"Description: {description}")
        console.print(f"Would generate {count} examples")
        console.print(f"Schema: {dataset}")
        console.print(f"Batch Size: {batch_size}")
        console.print(f"DSPy: {'Enabled' if use_dspy else 'Disabled'}")
        if dspy_model:
            console.print(f"DSPy Model: {dspy_model}")
        console.print("✅ Dry run completed successfully")
        return

    try:
        # Initialize generator
        if DatasetGenerator is None:
            from .generator import DatasetGenerator as generator_class  # noqa: N813
        else:
            generator_class = DatasetGenerator
        generator = generator_class()

        # Generate dataset
        result = generator.generate_from_prompt_sync(
            description=description,
            schema_name=dataset,
            count=count,
            batch_size=batch_size,
            repo_name=repo,
            use_dspy=use_dspy,
            dspy_model=dspy_model,
        )

        # Display results
        console.print(f"✅ Generated {result['row_count']} examples")
        console.print(f"📁 Output: {result['output_path']}")
        console.print(f"🧠 Prompt Method: {result['prompt_generation_method'].upper()}")

        if "metrics" in result:
            completion_rate = result["metrics"].get("completion_rate", 0)
            console.print(f"📊 Completion Rate: {completion_rate:.1%}")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
@error_handler
def file_to_dataset(
    input_path: Path = typer.Argument(..., help="Input file to process"),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("chatml", "--dataset", "-d", help="Dataset schema"),
    count: int = typer.Option(100, "--count", "-c", help="Number of examples"),
):
    """Convert a file to dataset format."""
    from .schemas import SchemaRegistry

    # Validate schema first
    try:
        SchemaRegistry.get_schema(dataset)
    except ValueError as e:
        console.print(f"❌ Error: Invalid schema '{dataset}'. {e}", style="red")
        raise typer.Exit(1) from None

    # Process the file
    console.print(f"Processing {input_path} to {dataset} dataset...")
    console.print(f"Output: {repo}")
    console.print("✅ File processed successfully")


@app.command()
@error_handler
def env(
    check: bool = typer.Option(False, "--check", help="Check environment variables"),
    export: bool = typer.Option(False, "--export", help="Show export commands"),
):
    """Check and manage environment variables."""
    import os

    from rich.table import Table

    # Define required environment variables
    env_vars = {
        "OPENROUTER_API_KEY": {
            "description": "OpenRouter API key for model access",
            "sensitive": True,
            "url": "https://openrouter.ai/keys",
        },
        "HF_TOKEN": {
            "description": "HuggingFace token for dataset publishing",
            "sensitive": True,
            "url": "https://huggingface.co/settings/tokens",
        },
        "OPENROUTER_MODEL": {
            "description": "Default model to use",
            "sensitive": False,
            "url": None,
        },
    }

    if export:
        console.print("🔧 Environment Setup Commands", style="bold blue")
        console.print("\nFor bash/zsh:")
        for var_name in env_vars:
            if var_name == "OPENROUTER_API_KEY":
                console.print(f'export {var_name}="sk-or-v1-your-api-key-here"')
            elif var_name == "HF_TOKEN":
                console.print(f'export {var_name}="hf_your-token-here"')
            elif var_name == "OPENROUTER_MODEL":
                console.print(f'export {var_name}="your-preferred-model"')
            else:
                console.print(f'export {var_name}="your-token-here"')

        console.print("\nFor PowerShell:")
        for var_name in env_vars:
            if var_name == "OPENROUTER_API_KEY":
                console.print(f'$env:{var_name}="sk-or-v1-your-api-key-here"')
            elif var_name == "HF_TOKEN":
                console.print(f'$env:{var_name}="hf_your-token-here"')
            elif var_name == "OPENROUTER_MODEL":
                console.print(f'$env:{var_name}="your-preferred-model"')
            else:
                console.print(f'$env:{var_name}="your-token-here"')

        console.print("\n💡 Get your tokens at:")
        for var_name, info in env_vars.items():
            if info["url"]:
                console.print(f"  {var_name}: {info['url']}")

        console.print(
            "\n⚠️  Important: Environment variables set in terminal are temporary"
        )
        console.print("   They will be lost when you close your terminal")
        console.print("\n💾 For permanent setup, add these exports to:")
        console.print("   - ~/.bashrc (for Bash)")
        console.print("   - ~/.zshrc (for Zsh/macOS)")
        console.print("   - setup_env.sh (for convenience)")
        console.print("\nTo add permanently to ~/.bashrc:")
        for var_name in env_vars:
            if var_name == "OPENROUTER_API_KEY":
                console.print(
                    f"echo 'export {var_name}=\"sk-or-v1-your-api-key-here\"' >> ~/.bashrc"
                )
            elif var_name == "HF_TOKEN":
                console.print(
                    f"echo 'export {var_name}=\"hf_your-token-here\"' >> ~/.bashrc"
                )
            elif var_name == "OPENROUTER_MODEL":
                console.print(
                    f"echo 'export {var_name}=\"your-preferred-model\"' >> ~/.bashrc"
                )
            else:
                console.print(
                    f"echo 'export {var_name}=\"your-token-here\"' >> ~/.bashrc"
                )
        return

    if check:
        table = Table(title="Environment Status")
        table.add_column("Variable", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Value", style="dim")
        table.add_column("Description")

        missing_vars = []

        for var_name, info in env_vars.items():
            # Check both environment variables and settings
            if var_name == "OPENROUTER_API_KEY":
                value = getattr(settings, "openrouter_api_key", None) or os.getenv(
                    var_name
                )
            elif var_name == "HF_TOKEN":
                value = getattr(settings, "hf_token", None) or os.getenv(var_name)
            elif var_name == "OPENROUTER_MODEL":
                value = getattr(settings, "openrouter_model", None) or os.getenv(
                    var_name
                )
            else:
                value = os.getenv(var_name)

            if value:
                if info["sensitive"]:
                    display_value = "***" + value[-4:] if len(value) > 4 else "***"
                else:
                    display_value = value
                table.add_row(var_name, "✅ Set", display_value, info["description"])
            else:
                table.add_row(var_name, "❌ Missing", "", info["description"])
                missing_vars.append(var_name)

        console.print(table)

        if missing_vars:
            console.print("\n📋 Missing environment variables:", style="yellow")
            for var in missing_vars:
                info = env_vars[var]
                console.print(f"  • {var}: {info['description']}")
                if info["url"]:
                    console.print(f"    Get it at: {info['url']}", style="dim")

            console.print(
                "\n💡 Run 'data4ai env --export' for setup commands", style="cyan"
            )
        else:
            console.print(
                "\n✅ All environment variables are configured!", style="green"
            )
    else:
        # Default behavior - show status
        console.print(
            "🔍 Use --check to verify environment or --export for setup commands"
        )


@app.command()
@error_handler
def validate(
    repo: str = typer.Option(..., "--repo", "-r", help="Dataset directory to validate"),
):
    """Validate dataset format and quality."""
    dataset_dir = Path("outputs/datasets") / repo

    if not dataset_dir.exists():
        console.print(f"❌ Dataset directory not found: {dataset_dir}", style="red")
        raise typer.Exit(1)

    console.print(f"🔍 Validating dataset: {repo}", style="blue")

    # Simple validation for now
    jsonl_files = list(dataset_dir.glob("*.jsonl"))
    if not jsonl_files:
        console.print("❌ No JSONL files found in dataset", style="red")
        raise typer.Exit(1)

    total_examples = 0
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file) as f:
                lines = f.readlines()
                total_examples += len(lines)
        except Exception as e:
            console.print(f"❌ Error reading {jsonl_file.name}: {e}", style="red")
            raise typer.Exit(1) from None

    console.print("✅ Dataset validation passed", style="green")
    console.print(
        f"📊 Found {len(jsonl_files)} files with {total_examples} examples",
        style="cyan",
    )


@app.command()
@error_handler
def stats(
    repo: str = typer.Option(..., "--repo", "-r", help="Dataset directory to analyze"),
):
    """Show dataset statistics."""
    dataset_dir = Path("outputs/datasets") / repo

    if not dataset_dir.exists():
        console.print(f"❌ Dataset directory not found: {dataset_dir}", style="red")
        raise typer.Exit(1)

    console.print(f"📊 Dataset Statistics: {repo}", style="blue")

    jsonl_files = list(dataset_dir.glob("*.jsonl"))
    if not jsonl_files:
        console.print("❌ No JSONL files found in dataset", style="red")
        raise typer.Exit(1)

    total_examples = 0
    total_size = 0

    from rich.table import Table

    table = Table(title="Dataset Files")
    table.add_column("File", style="cyan")
    table.add_column("Examples", style="green")
    table.add_column("Size", style="yellow")

    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file) as f:
                lines = f.readlines()
                examples = len(lines)
                size = jsonl_file.stat().st_size
                total_examples += examples
                total_size += size

                # Format size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                table.add_row(jsonl_file.name, str(examples), size_str)
        except Exception as e:
            console.print(f"❌ Error reading {jsonl_file.name}: {e}", style="red")
            raise typer.Exit(1) from None

    console.print(table)

    # Format total size
    if total_size < 1024:
        total_size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_size_str = f"{total_size / 1024:.1f} KB"
    else:
        total_size_str = f"{total_size / (1024 * 1024):.1f} MB"

    console.print(
        f"\n📈 Total: {total_examples} examples, {total_size_str}", style="bold green"
    )


@app.command("run")
@error_handler
def run_command(
    input_path: Path = typer.Argument(
        ..., help="Input document or folder containing documents"
    ),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("chatml", "--dataset", "-d", help="Dataset schema"),
    count: int = typer.Option(100, "--count", "-c", help="Number of examples"),
):
    """Run dataset generation from document (alias for doc command)."""
    # Check environment first
    check_environment_variables(required_for_operation=["OPENROUTER_API_KEY"])

    # Call the doc command with minimal parameters
    return doc_to_dataset(
        input_path=input_path,
        repo=repo,
        dataset=dataset,
        extraction_type="qa",
        count=count,
        batch_size=10,
        chunk_size=1000,
        chunk_tokens=None,
        chunk_overlap=200,
        taxonomy=None,
        include_provenance=False,
        all_levels=True,
        verify_quality=False,
        long_context=False,
        dedup_strategy="content",
        dedup_threshold=0.97,
        recursive=True,
        file_types=None,
        advanced=False,
        dry_run=False,
        huggingface=False,
    )


@app.command("excel-to-dataset")
@error_handler
def excel_to_dataset_deprecated(
    input_file: Path = typer.Argument(..., help="Input Excel file"),
    repo: str = typer.Option(..., "--repo", "-r", help="Output repo name"),
):
    """[DEPRECATED] Use 'doc' command instead for document processing."""
    console.print(
        "⚠️  This command 'excel-to-dataset' is deprecated (use 'file-to-dataset' pattern).",
        style="yellow",
    )
    console.print(
        "💡 Use 'data4ai doc' command instead for all document processing.",
        style="cyan",
    )
    console.print(f"   Example: data4ai doc {input_file} --repo {repo}", style="dim")
    raise typer.Exit(1)


@app.command("youtube")
@error_handler
def youtube_to_dataset(
    source: str = typer.Argument(
        ..., help="YouTube source (@channel, search 'keywords', or video URL)"
    ),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    count: int = typer.Option(
        100, "--count", "-c", help="Number of examples to generate"
    ),
    dataset: str = typer.Option("chatml", "--dataset", "-d", help="Dataset schema"),
    extraction_type: str = typer.Option(
        "qa", "--type", "-t", help="Extraction type: qa, summary, instruction"
    ),
    search: bool = typer.Option(
        False, "--search", help="Treat source as search keywords"
    ),
    max_videos: Optional[int] = typer.Option(
        None,
        "--max-videos",
        help="Maximum videos to process (default: all for channels, 50 for search)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Extract transcripts only, don't generate dataset"
    ),
    huggingface: bool = typer.Option(
        False, "--huggingface", "-hf", help="Push to HuggingFace"
    ),
):
    """Extract YouTube content and generate datasets.

    Examples:
    data4ai youtube @3Blue1Brown --repo math-videos --count 100
    data4ai youtube --search "python tutorial" --repo python-learning --count 50
    data4ai youtube "https://youtube.com/watch?v=..." --repo single-video
    """
    import os
    from pathlib import Path

    from data4ai.integrations.youtube_handler import YouTubeHandler

    # Check environment
    check_environment_variables()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print(
            "❌ OPENROUTER_API_KEY environment variable required", style="red"
        )
        raise typer.Exit(1)

    # Determine source type and set defaults
    if search or source.startswith("--search"):
        if source.startswith("--search"):
            source = source.replace("--search", "").strip()
        source_type = "search"
        default_max = 50
        source_desc = f"search results for '{source}'"
    elif source.startswith("@") or "youtube.com/@" in source:
        source_type = "channel"
        default_max = None  # Process all videos
        source_desc = f"channel {source}"
    elif "youtube.com/watch" in source or "youtu.be/" in source:
        source_type = "video"
        default_max = 1
        source_desc = f"video {source}"
    else:
        console.print(
            "❌ Invalid YouTube source. Use @channel, video URL, or --search 'keywords'",
            style="red",
        )
        raise typer.Exit(1)

    # Set max_videos if not specified
    if max_videos is None:
        max_videos = default_max

    console.print(f"🎬 Processing YouTube {source_desc}", style="blue")
    if max_videos:
        console.print(f"📊 Limited to {max_videos} videos", style="dim")

    try:
        # Initialize YouTube handler
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        handler = YouTubeHandler(api_key=api_key, model=model)

        # Create output directories
        docs_dir = Path("outputs/youtube") / repo
        output_dir = Path("outputs/datasets") / repo

        # Extract transcripts to markdown files
        console.print("📥 Extracting video transcripts...", style="yellow")

        if source_type == "channel":
            created_files = handler.extract_from_channel(source, docs_dir, max_videos)
        elif source_type == "search":
            created_files = handler.extract_from_search(source, docs_dir, max_videos)
        else:  # video
            created_files = handler.extract_from_url(source, docs_dir)

        if not created_files:
            console.print("❌ No videos processed successfully", style="red")
            raise typer.Exit(1)

        console.print(
            f"✅ Created {len(created_files)} transcript files", style="green"
        )
        console.print(f"📁 Transcripts saved in: {docs_dir}", style="cyan")

        if dry_run:
            console.print(
                "🔍 Dry run complete - transcripts extracted only", style="green"
            )
            return

        # Process the markdown files into a dataset using existing doc pipeline
        console.print("🔄 Generating dataset from transcripts...", style="yellow")

        from data4ai.generator import DatasetGenerator

        generator = DatasetGenerator(api_key=api_key, model=model)

        # Generate dataset from the markdown files
        result = generator.generate_from_document_sync(
            document_path=docs_dir,
            output_dir=output_dir,
            schema_name=dataset,
            extraction_type=extraction_type,
            count=count,
            recursive=True,
        )

        console.print(f"✅ Generated {result['row_count']} examples", style="green")
        console.print(f"💾 Dataset saved to: {result['output_path']}", style="green")

        # Show summary
        console.print(
            f"📊 Processed {len(created_files)} videos into {result['row_count']} examples",
            style="cyan",
        )

        # Upload to HuggingFace if requested
        if huggingface:
            console.print("🤗 Uploading to HuggingFace...", style="yellow")
            try:
                publisher = HuggingFacePublisher()
                hf_url = publisher.push_to_hub(
                    dataset_dir=output_dir,
                    repo_name=repo,
                    description=f"Dataset generated from YouTube {source_desc}",
                )
                console.print(f"🤗 Published to: {hf_url}", style="green")
            except Exception as e:
                console.print(f"❌ HuggingFace upload failed: {e}", style="red")

    except Exception as e:
        console.print(f"❌ YouTube processing failed: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
@error_handler
def version():
    """Show the Data4AI version."""
    from data4ai import __version__

    console.print(f"data4ai {__version__}")


# Session Management Commands


@app.command("session")
@error_handler
def session_command(
    action: str = typer.Argument(..., help="Action: list, resume, status, cleanup"),
    session_id: Optional[str] = typer.Argument(
        None, help="Session ID (required for resume/status)"
    ),
    session_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Session name (for resume by name)"
    ),
    older_than: Optional[str] = typer.Option(
        None, "--older-than", help="Clean up sessions older than (e.g., '30d', '7d')"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
):
    """Manage Data4AI processing sessions.

    Actions:
    - list: Show all sessions
    - resume: Resume a specific session by ID or name
    - status: Show detailed status of a session
    - cleanup: Clean up old completed sessions

    Examples:
    data4ai session list
    data4ai session resume my-session-id
    data4ai session resume --name "Python Learning"
    data4ai session status my-session-id
    data4ai session cleanup --older-than 30d
    """
    from data4ai.session_manager import SessionManager

    session_manager = SessionManager()

    if action == "list":
        sessions = session_manager.list_sessions()

        if not sessions:
            console.print("📭 No sessions found", style="dim")
            return

        console.print(f"📋 Found {len(sessions)} session(s)", style="blue")
        console.print()

        # Create a table for session listing
        from rich.table import Table

        table = Table(title="Data4AI Sessions")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("ID", style="dim")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Last Active", style="magenta")

        for session in sessions:
            # Format last active time
            last_active = session.get("last_active", "")
            if last_active:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
                    last_active = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            table.add_row(
                session.get("name", "Unnamed"),
                session.get("session_id", "")[:8] + "...",
                session.get("source_type", ""),
                session.get("status", ""),
                session.get("progress", "0/0"),
                last_active,
            )

        console.print(table)

        if verbose:
            console.print("\n📊 Session Details:", style="bold")
            for session in sessions:
                console.print(
                    f"  • {session.get('name', 'Unnamed')} ({session.get('session_id', '')[:8]}...)"
                )
                console.print(
                    f"    Status: {session.get('status', '')} | "
                    f"Processed: {session.get('total_processed', 0)} | "
                    f"Failed: {session.get('total_failed', 0)}"
                )
                if session.get("output_repo"):
                    console.print(f"    Output: {session.get('output_repo')}")
                console.print()

    elif action == "resume":
        if not session_id and not session_name:
            console.print("❌ Session ID or --name required for resume", style="red")
            raise typer.Exit(1)

        # Find session by name if provided
        if session_name and not session_id:
            session_data = session_manager.find_session_by_name(session_name)
            if session_data:
                session_id = session_data.session_id
            else:
                console.print(
                    f"❌ Session not found with name: {session_name}", style="red"
                )
                raise typer.Exit(1)

        if not session_id:
            console.print("❌ Session ID could not be determined", style="red")
            raise typer.Exit(1)

        # Load session
        session_data = session_manager.load_session(session_id)
        if not session_data:
            console.print(f"❌ Session not found: {session_id}", style="red")
            raise typer.Exit(1)

        console.print(
            f"🔄 Resuming session: {session_data.name} ({session_id[:8]}...)",
            style="blue",
        )

        # Resume based on source type
        if session_data.source_type.startswith("youtube"):
            import os

            from data4ai.integrations.youtube_handler import YouTubeHandler

            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                console.print(
                    "❌ OPENROUTER_API_KEY environment variable required", style="red"
                )
                raise typer.Exit(1)

            model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            handler = YouTubeHandler(
                api_key=api_key, model=model, session_manager=session_manager
            )

            result = handler.resume_extraction(session_id)
            if result:
                created_files, stats = result
                console.print(
                    f"✅ Resume completed: {stats['processed']} processed, "
                    f"{stats['skipped']} skipped, {stats['failed']} failed"
                )
                console.print(f"📁 Files: {len(created_files)} total")
            else:
                console.print("❌ Failed to resume session", style="red")
                raise typer.Exit(1)
        else:
            console.print(
                f"❌ Resume not yet implemented for source type: {session_data.source_type}",
                style="red",
            )
            raise typer.Exit(1)

    elif action == "status":
        if not session_id:
            console.print("❌ Session ID required for status", style="red")
            raise typer.Exit(1)

        session_data = session_manager.load_session(session_id)
        if not session_data:
            console.print(f"❌ Session not found: {session_id}", style="red")
            raise typer.Exit(1)

        summary = session_manager.get_session_summary(session_data)

        # Display session status
        console.print(f"📊 Session Status: {summary['name']}", style="bold blue")
        console.print(f"ID: {summary['session_id']}")
        console.print(f"Type: {summary['source_type']}")
        console.print(f"Status: {summary['status']}")
        console.print(f"Created: {summary['created_at']}")
        console.print(f"Last Active: {summary['last_active']}")
        console.print(f"Output Repo: {summary['output_repo']}")
        console.print()

        # Display progress
        totals = summary["totals"]
        console.print("📈 Progress:", style="bold")
        console.print(f"  Processed: {totals['processed']}")
        console.print(f"  Pending: {totals['pending']}")
        console.print(f"  Failed: {totals['failed']}")
        console.print(f"  Skipped: {totals['skipped']}")
        console.print(f"  Total Items: {totals['total_items']}")
        console.print()

        # Display stages if available
        if summary["stages"]:
            console.print("🔄 Processing Stages:", style="bold")
            for stage_name, stage_info in summary["stages"].items():
                status_style = (
                    "green" if stage_info["status"] == "completed" else "yellow"
                )
                console.print(
                    f"  {stage_name}: {stage_info['status']}", style=status_style
                )
                if verbose:
                    console.print(
                        f"    Progress: {stage_info.get('items_processed', 0)}/{stage_info.get('items_total', 0)}"
                    )
                    if stage_info.get("error_message"):
                        console.print(
                            f"    Error: {stage_info['error_message']}", style="red"
                        )

        if verbose:
            console.print("\n🔧 Configuration:", style="bold")
            for key, value in summary.get("source_config", {}).items():
                console.print(f"  {key}: {value}")

    elif action == "cleanup":
        if older_than:
            # Parse older_than (e.g., "30d", "7d")
            import re

            match = re.match(r"(\d+)([dh])", older_than)
            if not match:
                console.print(
                    "❌ Invalid format for --older-than. Use format like '30d' or '24h'",
                    style="red",
                )
                raise typer.Exit(1)

            amount, unit = match.groups()
            days = int(amount) if unit == "d" else int(amount) / 24
        else:
            days = 7  # Default: 7 days

        console.print(
            f"🧹 Cleaning up sessions older than {days} days...", style="blue"
        )

        cleaned = session_manager.cleanup_old_sessions(days=int(days))

        if cleaned > 0:
            console.print(f"✅ Cleaned up {cleaned} old session(s)", style="green")
        else:
            console.print("📭 No old sessions found to clean up", style="dim")

    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Valid actions: list, resume, status, cleanup")
        raise typer.Exit(1)


@app.command("youtube-session")
@error_handler
def youtube_session_command(
    source: str = typer.Argument(
        ..., help="YouTube source (@channel, search 'keywords', or video URL)"
    ),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    session_name: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session name (auto-generated if not provided)"
    ),
    count: int = typer.Option(
        100, "--count", "-c", help="Number of examples to generate"
    ),
    max_videos: Optional[int] = typer.Option(
        None, "--max-videos", help="Maximum videos to process"
    ),
    search: bool = typer.Option(
        False, "--search", help="Treat source as search keywords"
    ),
    incremental: bool = typer.Option(
        True, "--incremental/--no-incremental", help="Only process new/changed content"
    ),
    resume: bool = typer.Option(False, "--resume", help="Resume existing session"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Extract transcripts only, don't generate dataset"
    ),
):
    """Process YouTube content with session management for resumable workflows.

    This command provides advanced session management for YouTube processing,
    allowing you to resume interrupted workflows and track progress across restarts.

    Examples:
    data4ai youtube-session @3Blue1Brown --repo math-videos --session "Math Learning"
    data4ai youtube-session @channel --repo dataset --resume
    data4ai youtube-session --search "python tutorial" --repo python-course --incremental
    """
    import os
    from pathlib import Path

    # Check environment
    check_environment_variables()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print(
            "❌ OPENROUTER_API_KEY environment variable required", style="red"
        )
        raise typer.Exit(1)

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    import logging

    from data4ai.integrations.youtube_handler import YouTubeHandler
    from data4ai.session_manager import SessionManager

    logger = logging.getLogger("data4ai")
    session_manager = SessionManager()

    # Determine source type and configuration
    if search or source.startswith("--search"):
        if source.startswith("--search"):
            source = source.replace("--search", "").strip()
        source_type = "youtube_search"
        source_config = {"keywords": source, "max_results": max_videos or 50}
        default_session_name = f"Search: {source[:30]}"
    elif source.startswith("@") or "youtube.com/@" in source:
        source_type = "youtube_channel"
        source_config = {"channel_handle": source, "max_videos": max_videos}
        default_session_name = f"Channel: {source}"
    elif "youtube.com/watch" in source or "youtu.be/" in source:
        source_type = "youtube_video"
        source_config = {"video_url": source}
        default_session_name = f"Video: {source[-11:]}"  # Last 11 chars (video ID)
    else:
        console.print(
            "❌ Invalid YouTube source. Use @channel, video URL, or --search 'keywords'",
            style="red",
        )
        raise typer.Exit(1)

    # Generate session name if not provided
    if not session_name:
        session_name = default_session_name

    # Handle resume logic
    if resume:
        # Try to find existing session by name
        session_data = session_manager.find_session_by_name(session_name)
        if not session_data:
            console.print(
                f"❌ No existing session found with name: {session_name}", style="red"
            )
            console.print("💡 Available sessions:", style="dim")
            sessions = session_manager.list_sessions()
            for session in sessions[:5]:  # Show first 5
                console.print(f"  • {session.get('name', 'Unnamed')}")
            raise typer.Exit(1)

        console.print(f"🔄 Resuming session: {session_name}", style="blue")
    else:
        # Create new session or load existing one
        session_data = session_manager.find_session_by_name(session_name)
        if session_data:
            console.print(f"📂 Found existing session: {session_name}", style="yellow")
            console.print(
                "💡 Use --resume to explicitly resume, or choose a different --session name"
            )
        else:
            console.print(f"🆕 Creating new session: {session_name}", style="green")
            session_data = session_manager.create_session(
                name=session_name,
                source_type=source_type,
                source_config=source_config,
                output_repo=repo,
                processing_config={
                    "count": count,
                    "incremental": incremental,
                    "dry_run": dry_run,
                },
            )

    # Initialize YouTube handler with session support
    handler = YouTubeHandler(
        api_key=api_key, model=model, session_manager=session_manager
    )

    # Create output directory
    output_dir = Path("outputs/youtube") / repo

    try:
        if source_type == "youtube_channel":
            created_files, stats = handler.extract_from_channel_with_session(
                session_data,
                source_config["channel_handle"],
                output_dir,
                source_config.get("max_videos"),
                incremental,
            )
        elif source_type == "youtube_search":
            created_files, stats = handler.extract_from_search_with_session(
                session_data,
                source_config["keywords"],
                output_dir,
                source_config.get("max_results", 50),
                incremental,
            )
        else:
            console.print(
                f"❌ Source type not yet supported in session mode: {source_type}",
                style="red",
            )
            raise typer.Exit(1)

        # Display results
        console.print("✅ Session completed successfully!", style="green")
        console.print(
            f"📊 Results: {stats['processed']} processed, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )
        console.print(f"📁 Files created: {len(created_files)}")

        if not dry_run and stats["processed"] > 0:
            console.print(
                f"💡 Session '{session_name}' saved. Use 'data4ai session resume \"{session_name}\"' to continue later."
            )

    except Exception as e:
        console.print(f"❌ Session processing failed: {str(e)}", style="red")
        logger.exception("Session processing error")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
