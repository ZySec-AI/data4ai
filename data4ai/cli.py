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

# Placeholder for tests to patch without importing heavy modules at import time.
# The real import happens lazily inside command functions.
DatasetGenerator = None  # type: ignore


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
def prompt(
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("chatml", "--dataset", "-d", help="Dataset schema"),
    description: str = typer.Option(
        ..., "--description", "-desc", help="Dataset description"
    ),
    count: int = typer.Option(100, "--count", "-c", help="Number of examples"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Temperature"),
    batch_size: int = typer.Option(10, "--batch-size", help="Batch size"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without generating"),
    use_dspy: bool = typer.Option(
        True, "--use-dspy/--no-use-dspy", help="Use DSPy for dynamic prompt generation"
    ),
    taxonomy: Optional[str] = typer.Option(
        None,
        "--taxonomy",
        help="Bloom taxonomy for prompt flow: balanced, basic, advanced",
    ),
    all_levels: bool = typer.Option(
        False,
        "--all-levels/--no-all-levels",
        help="QA: ensure all Bloom levels coverage in prompt flow",
    ),
):
    """Generate dataset from natural language description."""
    # Check for required environment variables upfront
    if not model and not settings.openrouter_api_key:
        check_environment_variables(required_for_operation=["OPENROUTER_API_KEY"])
        raise typer.Exit(1)

    if dry_run:
        console.print(f"🔍 Would generate {count} {dataset} examples", style="yellow")
        console.print(f"📝 Description: {description}", style="cyan")
        console.print(
            f"📁 Output directory: {settings.output_dir / repo}", style="cyan"
        )
        console.print("✅ Dry run completed successfully", style="green")
        return

    console.print(f"Generating {count} examples...", style="blue")

    # Lazy import to avoid heavy dependencies at CLI import time
    from data4ai.generator import DatasetGenerator

    # Initialize generator with configuration
    generator = DatasetGenerator(
        model=model,
        temperature=temperature,
        seed=seed,
    )

    # Override to use static prompt generator (no DSPy) if specified
    if not use_dspy:
        generator.use_static_prompt_generator()

    # Generate dataset
    output_path = settings.output_dir / repo
    with console.status(f"Generating {dataset} dataset..."):
        result = generator.generate_from_prompt_sync(
            description=description,
            output_dir=output_path,
            schema_name=dataset,
            count=count,
            batch_size=batch_size,
            dry_run=dry_run,
            taxonomy=taxonomy,
            taxonomy_all_levels=all_levels,
        )

    console.print(f"✅ Generated {result['row_count']} examples", style="green")
    console.print(f"💾 Saved to: {result['output_path']}", style="green")

    # Show prompt information
    prompt_method = result.get("prompt_generation_method", "unknown")
    console.print(f"🔮 Prompt Method: {prompt_method.upper()}", style="cyan")

    # Show metrics
    metrics = result.get("metrics", {})
    if metrics:
        console.print(
            f"📈 Completion rate: {metrics.get('completion_rate', 0):.1%}",
            style="cyan",
        )

    # Show usage
    usage = result.get("usage", {})
    if usage.get("total_tokens"):
        console.print(f"📊 Tokens used: {usage['total_tokens']:,}", style="cyan")
        console.print(
            f"💰 Estimated cost: ${usage.get('estimated_cost', 0):.4f}",
            style="cyan",
        )


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


if __name__ == "__main__":
    app()
