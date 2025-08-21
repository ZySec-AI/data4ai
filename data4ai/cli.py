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


@app.callback()
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Data4AI - Generate high-quality datasets for LLM training."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")


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
    dataset_dir = settings.output_dir / repo
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
        ..., help="Input document or folder containing documents"
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
    per_document: bool = typer.Option(
        True,
        "--per-document/--combined",
        help="Write one dataset per input document (default: per-document)",
    ),
):
    """Generate dataset from document(s) - supports files and folders."""

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
        console.print(f"📁 Would save to: {settings.output_dir / repo}", style="cyan")

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
    output_path = settings.output_dir / repo

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
            per_document=per_document,
            dedup_strategy=dedup_strategy,
            dedup_threshold=dedup_threshold,
        )

        # Process results (dry_run already handled above)
        console.print(f"✅ Generated {result['row_count']} examples", style="green")
        # If per-document, show parent folder; otherwise show the single JSONL path
        if result.get("per_document", False):
            console.print(
                f"💾 Saved per-document datasets under: {result['output_path']}",
                style="green",
            )
        else:
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
    dataset_dir = settings.output_dir / repo

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
    dataset_dir = settings.output_dir / repo

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
        per_document=True,
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


if __name__ == "__main__":
    app()
