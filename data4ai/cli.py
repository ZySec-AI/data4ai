"""CLI commands for Data4AI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from data4ai import __version__
from data4ai.client import OpenRouterConfig, SyncOpenRouterClient
from data4ai.config import settings
from data4ai.csv_handler import CSVHandler
from data4ai.error_handler import ErrorHandler, error_handler
from data4ai.excel_handler import ExcelHandler
from data4ai.generator import DatasetGenerator
from data4ai.integrations.dspy_prompts import create_prompt_generator
from data4ai.publisher import HuggingFacePublisher
from data4ai.schemas import SchemaRegistry
from data4ai.utils import (
    calculate_metrics,
    format_file_size,
    read_jsonl,
    setup_logging,
)

app = typer.Typer(
    name="data4ai",
    help="AI-powered dataset generation for instruction tuning",
    add_completion=False,
)
console = Console()


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
def create_sample(
    path: Path = typer.Argument(..., help="Output file path (Excel or CSV)"),
    schema: str = typer.Option("alpaca", "--schema", "-s", help="Dataset schema"),
    format: str = typer.Option(
        "excel", "--format", "-f", help="Output format: excel or csv"
    ),
):
    """Create a template file for the specified schema."""
    console.print(f"Creating {schema} template ({format} format)...", style="blue")

    if format.lower() == "csv":
        CSVHandler.create_template(path, schema)
    else:
        ExcelHandler.create_template(path, schema)

    console.print(f"✅ Template created: {path}", style="green")
    console.print("📝 Open the file and fill in your data", style="yellow")


@app.command()
@error_handler
def file_to_dataset(
    input_path: Path = typer.Argument(..., help="Input file (Excel or CSV)"),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("alpaca", "--dataset", "-d", help="Dataset schema"),
    delimiter: Optional[str] = typer.Option(
        None, "--delimiter", help="CSV delimiter (auto-detect if not specified)"
    ),
):
    """Convert filled Excel/CSV file to dataset without AI completion."""
    try:
        file_type = "CSV" if input_path.suffix.lower() == ".csv" else "Excel"
        console.print(f"Converting {file_type} to {dataset} dataset...", style="blue")

        # Read file
        if input_path.suffix.lower() == ".csv":
            df = CSVHandler.read_data(input_path, delimiter=delimiter)
            handler = CSVHandler
        else:
            df = ExcelHandler.read_data(input_path)
            handler = ExcelHandler

        console.print(f"📊 Read {len(df)} rows from {file_type}", style="cyan")

        # Validate schema
        is_valid, missing = handler.validate_schema_compatibility(df, dataset)
        if not is_valid:
            console.print(
                f"❌ Missing required columns: {', '.join(missing)}", style="red"
            )
            raise typer.Exit(1) from None

        # Convert to dataset
        dataset_data = handler.convert_to_dataset(df, dataset)
        console.print(f"✅ Converted {len(dataset_data)} valid examples", style="green")

        # Write output
        output_path = settings.output_dir / repo
        output_path.mkdir(parents=True, exist_ok=True)
        from data4ai.utils import save_metadata, write_jsonl

        jsonl_path = output_path / "data.jsonl"
        write_jsonl(dataset_data, jsonl_path)

        # Calculate metrics
        metrics = calculate_metrics(dataset_data, dataset)

        # Save metadata
        save_metadata(
            output_path,
            dataset,
            "manual",
            len(dataset_data),
            {"source": str(input_path)},
            metrics,
        )

        console.print(f"💾 Dataset saved to: {jsonl_path}", style="green")
        console.print(
            f"📈 Metrics: {metrics['total_rows']} rows, "
            f"{metrics['completion_rate']:.1%} complete",
            style="cyan",
        )

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


# Keep backward compatibility
@app.command()
def excel_to_dataset(
    excel_path: Path = typer.Argument(..., help="Input Excel file"),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("alpaca", "--dataset", "-d", help="Dataset schema"),
):
    """Convert filled Excel file to dataset without AI completion (deprecated, use file-to-dataset)."""
    console.print(
        "⚠️  This command is deprecated. Please use 'file-to-dataset' instead.",
        style="yellow",
    )
    file_to_dataset(excel_path, repo, dataset)


@app.command()
@error_handler
def run(
    input_path: Path = typer.Argument(..., help="Input file (Excel or CSV)"),
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("alpaca", "--dataset", "-d", help="Dataset schema"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Temperature"),
    max_rows: Optional[int] = typer.Option(
        None, "--max-rows", help="Max rows to generate"
    ),
    batch_size: int = typer.Option(10, "--batch-size", help="Batch size"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed"),
    delimiter: Optional[str] = typer.Option(
        None, "--delimiter", help="CSV delimiter (auto-detect if not specified)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without generating"),
):
    """Process Excel/CSV file with AI completion for partial rows."""
    try:
        if dry_run:
            console.print("🔍 Dry run mode - previewing only", style="yellow")
            console.print(f"📁 Input file: {input_path}", style="cyan")
            console.print(
                f"📁 Output directory: {settings.output_dir / repo}", style="cyan"
            )
            console.print("✅ Dry run completed successfully", style="green")
            return

        file_type = "CSV" if input_path.suffix.lower() == ".csv" else "Excel"
        console.print(f"Processing {file_type} with {dataset} schema...", style="blue")

        # Initialize generator
        generator = DatasetGenerator(
            model=model,
            temperature=temperature,
            seed=seed,
        )

        # Generate dataset based on file type
        output_path = settings.output_dir / repo
        with console.status("Generating dataset..."):
            if input_path.suffix.lower() == ".csv":
                result = generator.generate_from_csv_sync(
                    csv_path=input_path,
                    output_dir=output_path,
                    schema_name=dataset,
                    max_rows=max_rows,
                    batch_size=batch_size,
                    delimiter=delimiter,
                    dry_run=dry_run,
                )
            else:
                result = generator.generate_from_excel_sync(
                    excel_path=input_path,
                    output_dir=output_path,
                    schema_name=dataset,
                    max_rows=max_rows,
                    batch_size=batch_size,
                    dry_run=dry_run,
                )

        if dry_run:
            console.print(
                f"Would process {result.get('partial_rows', 0)} partial rows",
                style="cyan",
            )
        else:
            console.print(f"✅ Generated {result['row_count']} examples", style="green")
            console.print(f"💾 Saved to: {result['output_path']}", style="green")

            # Show usage stats
            usage = result.get("usage", {})
            if usage.get("total_tokens"):
                console.print(
                    f"📊 Tokens used: {usage['total_tokens']:,}", style="cyan"
                )
                console.print(
                    f"💰 Estimated cost: ${usage.get('estimated_cost', 0):.4f}",
                    style="cyan",
                )

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
@error_handler
def prompt(
    repo: str = typer.Option(
        ..., "--repo", "-r", help="Output directory and repo name"
    ),
    dataset: str = typer.Option("alpaca", "--dataset", "-d", help="Dataset schema"),
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
):
    """Generate dataset from natural language description."""
    try:
        if dry_run:
            console.print(
                f"🔍 Would generate {count} {dataset} examples", style="yellow"
            )
            console.print(f"📝 Description: {description}", style="cyan")
            console.print(
                f"📁 Output directory: {settings.output_dir / repo}", style="cyan"
            )
            console.print("✅ Dry run completed successfully", style="green")
            return

        console.print(f"Generating {count} examples...", style="blue")

        # Initialize generator with DSPy configuration
        generator = DatasetGenerator(
            model=model,
            temperature=temperature,
            seed=seed,
        )

        # Override DSPy setting if specified
        if not use_dspy:
            generator.prompt_generator = create_prompt_generator(
                model_name=model or settings.openrouter_model, use_dspy=False
            )

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

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


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
    try:
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

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
@error_handler
def validate(
    repo: str = typer.Option(..., "--repo", "-r", help="Dataset directory"),
    dataset: str = typer.Option("alpaca", "--dataset", "-d", help="Expected schema"),
):
    """Validate dataset quality and schema compliance."""
    try:
        console.print("Validating dataset...", style="blue")

        # Read dataset
        jsonl_path = Path(repo) / "data.jsonl"
        if not jsonl_path.exists():
            console.print(f"❌ Dataset not found: {jsonl_path}", style="red")
            raise typer.Exit(1) from None

        dataset_data = list(read_jsonl(jsonl_path))
        console.print(f"📊 Read {len(dataset_data)} examples", style="cyan")

        # Validate schema
        schema_registry = SchemaRegistry()
        valid_count = 0
        invalid_examples = []

        for i, entry in enumerate(dataset_data):
            if schema_registry.validate(entry, dataset):
                valid_count += 1
            else:
                invalid_examples.append(i)

        # Calculate metrics
        metrics = calculate_metrics(dataset_data, dataset)

        # Display results
        table = Table(title="Validation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Examples", str(len(dataset_data)))
        table.add_row("Valid Examples", str(valid_count))
        table.add_row("Invalid Examples", str(len(invalid_examples)))
        table.add_row("Completion Rate", f"{metrics['completion_rate']:.1%}")
        table.add_row(
            "Avg Instruction Length", f"{metrics['avg_instruction_length']:.0f}"
        )
        table.add_row("Avg Output Length", f"{metrics['avg_output_length']:.0f}")

        console.print(table)

        if invalid_examples:
            console.print(
                f"⚠️  Invalid examples at indices: {invalid_examples[:10]}...",
                style="yellow",
            )
        else:
            console.print("✅ All examples are valid!", style="green")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
@error_handler
def stats(
    repo: str = typer.Option(..., "--repo", "-r", help="Dataset directory"),
):
    """Display dataset statistics and metrics."""
    try:
        console.print("Analyzing dataset...", style="blue")

        # Read dataset
        jsonl_path = Path(repo) / "data.jsonl"
        if not jsonl_path.exists():
            console.print(f"❌ Dataset not found: {jsonl_path}", style="red")
            raise typer.Exit(1) from None

        dataset = list(read_jsonl(jsonl_path))

        # Detect schema
        schema = "alpaca"  # Default
        if dataset and "conversations" in dataset[0]:
            schema = "sharegpt"
        elif dataset and "response" in dataset[0]:
            schema = "dolly"

        # Calculate metrics
        metrics = calculate_metrics(dataset, schema)

        # File size
        file_size = jsonl_path.stat().st_size

        # Display statistics
        table = Table(title="Dataset Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("File Size", format_file_size(file_size))
        table.add_row("Schema", schema)
        table.add_row("Total Rows", str(metrics["total_rows"]))
        table.add_row("Empty Rows", str(metrics["empty_rows"]))
        table.add_row("Completion Rate", f"{metrics['completion_rate']:.1%}")
        table.add_row(
            "Avg Instruction Length", f"{metrics['avg_instruction_length']:.0f}"
        )
        table.add_row("Min Instruction Length", str(metrics["min_instruction_length"]))
        table.add_row("Max Instruction Length", str(metrics["max_instruction_length"]))
        table.add_row("Avg Output Length", f"{metrics['avg_output_length']:.0f}")
        table.add_row("Min Output Length", str(metrics["min_output_length"]))
        table.add_row("Max Output Length", str(metrics["max_output_length"]))

        console.print(table)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command("list-models")
@error_handler
def list_models():
    """Show available OpenRouter models."""
    console.print("Fetching available models...", style="blue")

    # Check if API key is set
    if not settings.openrouter_api_key:
        console.print(ErrorHandler.get_message("api_key_missing"), style="red")
        raise typer.Exit(1) from None

    config = OpenRouterConfig(
        api_key=settings.openrouter_api_key,
        site_url=settings.site_url,
        site_name=settings.site_name,
    )
    client = SyncOpenRouterClient(config)
    models = client.list_models()

    # Display models
    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Context Length", style="green")
    table.add_column("Price/1M tokens", style="yellow")

    for model in models[:20]:  # Show top 20
        pricing = model.get("pricing", {}).get("prompt", 0)
        try:
            price_str = f"${float(pricing) * 1000:.2f}" if pricing else "N/A"
        except (ValueError, TypeError):
            price_str = "N/A"

        table.add_row(
            model.get("id", ""),
            str(model.get("context_length", "")),
            price_str,
        )

    console.print(table)
    console.print(f"\n📊 Total models available: {len(models)}", style="cyan")


@app.command("config")
def config(
    show: bool = typer.Option(True, "--show", help="Show current configuration"),
    save: bool = typer.Option(False, "--save", help="Save configuration to file"),
):
    """Display or save current configuration."""
    try:
        if save:
            settings.save_to_yaml()
            console.print(
                f"✅ Configuration saved to: {settings.get_config_path()}",
                style="green",
            )

        if show:
            table = Table(title="Current Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            # Show non-sensitive settings
            table.add_row("Model", settings.openrouter_model)
            table.add_row("Temperature", str(settings.temperature))
            table.add_row("Max Rows", str(settings.max_rows))
            table.add_row("Batch Size", str(settings.batch_size))
            table.add_row("Default Schema", settings.default_schema)
            table.add_row("Output Directory", str(settings.output_dir))
            table.add_row("Site URL", settings.site_url)
            table.add_row("Site Name", settings.site_name)
            table.add_row("HF Organization", settings.hf_organization or "Not set")
            table.add_row("API Key Set", "✅" if settings.openrouter_api_key else "❌")
            table.add_row("HF Token Set", "✅" if settings.hf_token else "❌")

            console.print(table)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
def version():
    """Show Data4AI version."""
    console.print(f"Data4AI version {__version__}", style="cyan")


if __name__ == "__main__":
    app()
