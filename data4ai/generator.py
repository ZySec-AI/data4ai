"""Core dataset generation engine."""

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from data4ai.client import OpenRouterClient, OpenRouterConfig
from data4ai.config import settings
from data4ai.excel_handler import ExcelHandler
from data4ai.csv_handler import CSVHandler
from data4ai.exceptions import GenerationError, ValidationError, ConfigurationError
from data4ai.error_handler import async_error_handler, ErrorHandler
from data4ai.schemas import SchemaRegistry
from data4ai.utils import (
    batch_items,
    calculate_metrics,
    extract_json_from_text,
    save_metadata,
    write_jsonl,
)
from data4ai.integrations.dspy_prompts import create_prompt_generator


logger = logging.getLogger("data4ai")


class DatasetGenerator:
    """Core dataset generation engine."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ):
        """Initialize generator with configuration."""
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise ConfigurationError(
                ErrorHandler.get_message("api_key_missing")
            )
        
        self.model = model or settings.openrouter_model
        self.temperature = temperature or settings.temperature
        self.seed = seed or settings.seed
        
        # Set random seed if provided
        if self.seed:
            random.seed(self.seed)
        
        # Initialize API client with proper attribution
        config = OpenRouterConfig(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            site_url=settings.site_url,
            site_name=settings.site_name,
        )
        self.client = OpenRouterClient(config)
        
        # Load schema registry
        self.schemas = SchemaRegistry()
        
        # Initialize DSPy prompt generator
        self.prompt_generator = create_prompt_generator(
            model_name=self.model,
            use_dspy=settings.use_dspy
        )
    
    @async_error_handler
    async def generate_from_excel(
        self,
        excel_path: Path,
        output_dir: Path,
        schema_name: str,
        max_rows: Optional[int] = None,
        batch_size: int = 10,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Generate dataset from Excel template with partial data."""
        try:
            # Read Excel file
            df = ExcelHandler.read_data(excel_path)
            
            # Validate schema compatibility
            is_valid, missing_cols = ExcelHandler.validate_schema_compatibility(
                df, schema_name
            )
            if not is_valid:
                raise ValidationError(
                    f"Excel file missing required columns: {', '.join(missing_cols)}"
                )
            
            # Detect partial rows
            partial_rows = ExcelHandler.detect_partial_rows(df)
            
            if not partial_rows:
                logger.info("No partial rows found. Converting existing data.")
                dataset = ExcelHandler.convert_to_dataset(df, schema_name)
            else:
                # Limit rows if specified
                if max_rows:
                    partial_rows = partial_rows[:max_rows]
                
                logger.info(f"Found {len(partial_rows)} partial rows to complete")
                
                if dry_run:
                    logger.info("Dry run mode - skipping generation")
                    return {
                        "partial_rows": len(partial_rows),
                        "dry_run": True,
                    }
                
                # Generate completions for partial rows
                completed_data = await self._complete_partial_rows(
                    df, partial_rows, schema_name, batch_size
                )
                
                # Merge completed data
                for idx, data in completed_data.items():
                    for key, value in data.items():
                        if key in df.columns:
                            df.at[idx, key] = value
                
                # Convert to dataset format
                dataset = ExcelHandler.convert_to_dataset(df, schema_name)
            
            # Write output
            output_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = output_dir / "data.jsonl"
            write_jsonl(dataset, jsonl_path)
            
            # Calculate metrics
            metrics = calculate_metrics(dataset, schema_name)
            
            # Save metadata
            parameters = {
                "temperature": self.temperature,
                "batch_size": batch_size,
                "seed": self.seed,
                "source": str(excel_path),
            }
            save_metadata(output_dir, schema_name, self.model, len(dataset), parameters, metrics)
            
            # Save completed Excel
            if partial_rows:
                completed_excel_path = output_dir / "completed.xlsx"
                ExcelHandler.write_completed_data(df, completed_data, completed_excel_path)
            
            logger.info(f"Generated {len(dataset)} examples")
            
            return {
                "row_count": len(dataset),
                "output_path": str(jsonl_path),
                "metrics": metrics,
            }
            
        except Exception as e:
            logger.error(f"Generation from Excel failed: {e}")
            raise GenerationError(f"Failed to generate from Excel: {str(e)}")
    
    @async_error_handler
    async def generate_from_prompt(
        self,
        description: str,
        output_dir: Path,
        schema_name: str,
        count: int = 100,
        batch_size: int = 10,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Generate dataset from natural language description."""
        try:
            if dry_run:
                logger.info(f"Dry run: Would generate {count} examples")
                return {"count": count, "dry_run": True}
            
            logger.info(f"Generating {count} examples from description")
            
            # Generate prompt once for the entire generation
            logger.info("Generating prompt for entire dataset...")
            master_prompt = self._build_generation_prompt(
                description, schema_name, count, None  # No previous examples for master prompt
            )
            
            # Track if DSPy was actually used
            dspy_used = hasattr(self, 'prompt_generator') and hasattr(self.prompt_generator, 'optimizer')
            
            # Generate in batches using the same master prompt
            dataset = []
            prompts_used = []  # Track prompts for audit
            
            for batch_start in range(0, count, batch_size):
                batch_count = min(batch_size, count - batch_start)
                
                # Use the master prompt for all batches
                prompt = master_prompt
                
                # Store prompt for audit
                prompts_used.append({
                    "batch": batch_start // batch_size + 1,
                    "prompt": prompt,
                    "examples_requested": batch_count,
                    "prompt_type": "master_dspy_prompt"
                })
                
                # Get completion with retry logic
                max_retries = 3
                entries = []
                
                for attempt in range(max_retries):
                    try:
                        messages = [{"role": "user", "content": prompt}]
                        response = await self.client.chat_completion(
                            messages,
                            temperature=self.temperature,
                            max_tokens=2000 * batch_count,
                        )
                        response_text = response["choices"][0]["message"]["content"]
                        
                        # Parse response
                        entries = self._parse_response(response_text, schema_name)
                        
                        if entries:
                            break  # Success, exit retry loop
                        else:
                            logger.warning(f"Batch {batch_start//batch_size + 1} returned no valid entries (attempt {attempt + 1}/{max_retries})")
                            
                    except Exception as e:
                        logger.warning(f"Batch {batch_start//batch_size + 1} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        if attempt == max_retries - 1:
                            logger.error(f"Failed to generate batch {batch_start//batch_size + 1} after {max_retries} attempts")
                
                dataset.extend(entries)
                logger.info(f"Generated {len(dataset)}/{count} examples")
            
            # Write output
            output_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = output_dir / "data.jsonl"
            write_jsonl(dataset, jsonl_path)
            
            # Calculate metrics
            metrics = calculate_metrics(dataset, schema_name)
            
            # Save metadata with prompts for audit
            parameters = {
                "temperature": self.temperature,
                "batch_size": batch_size,
                "seed": self.seed,
                "description": description,
                "prompts_used": prompts_used,  # Include prompts for audit
                "master_prompt": master_prompt,  # Include the master prompt
                "prompt_generation_method": "dspy" if dspy_used else "static"
            }
            save_metadata(output_dir, schema_name, self.model, len(dataset), parameters, metrics)
            
            logger.info(f"Generated {len(dataset)} examples")
            
            return {
                "row_count": len(dataset),
                "output_path": str(jsonl_path),
                "metrics": metrics,
                "prompts_used": prompts_used,
                "master_prompt": master_prompt,
                "prompt_generation_method": "dspy" if dspy_used else "static"
            }
            
        except Exception as e:
            logger.error(f"Generation from prompt failed: {e}")
            raise GenerationError(f"Failed to generate from prompt: {str(e)}")
    
    def generate_from_excel_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for generate_from_excel."""
        return asyncio.run(self.generate_from_excel(*args, **kwargs))
    
    def generate_from_prompt_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for generate_from_prompt."""
        return asyncio.run(self.generate_from_prompt(*args, **kwargs))
    
    async def _complete_partial_rows(
        self,
        df: pd.DataFrame,
        partial_rows: List[int],
        schema_name: str,
        batch_size: int,
    ) -> Dict[int, Dict[str, Any]]:
        """Complete partial rows using AI with enhanced progress tracking."""
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        from rich.console import Console
        
        console = Console()
        completed_data = {}
        total_rows = len(partial_rows)
        
        # Initialize metrics
        successful = 0
        failed = 0
        total_tokens = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[success]} success, {task.fields[failed]} failed[/cyan]"),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(
                f"Completing {total_rows} partial rows",
                total=total_rows,
                success=0,
                failed=0
            )
            
            for batch_num, batch in enumerate(batch_items(partial_rows, batch_size)):
                prompts = []
                for idx in batch:
                    row = df.iloc[idx]
                    prompt = self._build_completion_prompt(row, schema_name)
                    prompts.append((idx, prompt))
                
                # Get completions (process in parallel)
                tasks = []
                for idx, prompt in prompts:
                    messages = [{"role": "user", "content": prompt}]
                    api_task = self.client.chat_completion(
                        messages,
                        temperature=self.temperature,
                        max_tokens=1000,
                    )
                    tasks.append((idx, api_task))
                
                responses = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )
                
                # Parse responses
                for (idx, _), response in zip(tasks, responses):
                    try:
                        if isinstance(response, Exception):
                            logger.warning(f"API call failed for row {idx}: {response}")
                            completed_data[idx] = {}
                            failed += 1
                        else:
                            response_text = response["choices"][0]["message"]["content"]
                            parsed = self._parse_completion_response(response_text, schema_name)
                            completed_data[idx] = parsed
                            successful += 1
                            
                            # Track tokens
                            if "usage" in response:
                                total_tokens += response["usage"].get("total_tokens", 0)
                    except Exception as e:
                        logger.warning(f"Failed to parse completion for row {idx}: {e}")
                        completed_data[idx] = {}
                        failed += 1
                    
                    progress.update(
                        task,
                        advance=1,
                        success=successful,
                        failed=failed
                    )
                
                # Show batch metrics
                if hasattr(self.client, 'get_metrics'):
                    metrics = self.client.get_metrics()
                    if metrics["requests_per_minute"] > 0:
                        console.print(
                            f"[dim]Batch {batch_num + 1}: "
                            f"RPM: {metrics['requests_per_minute']}, "
                            f"Avg latency: {metrics['avg_latency']:.2f}s[/dim]"
                        )
        
        # Summary
        console.print(f"\n[green]✓[/green] Completed {successful}/{total_rows} rows")
        if failed > 0:
            console.print(f"[yellow]⚠[/yellow] {failed} rows failed")
        if total_tokens > 0:
            console.print(f"[cyan]📊[/cyan] Total tokens: {total_tokens:,}")
        
        return completed_data
    
    def _build_generation_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        previous_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build dynamic prompt using DSPy for generating examples from description."""
        try:
            # Use DSPy to generate dynamic, high-quality prompts
            if previous_examples:
                # Use adaptive prompting with previous examples
                prompt = self.prompt_generator.generate_adaptive_prompt(
                    description=description,
                    schema_name=schema_name,
                    count=count,
                    previous_examples=previous_examples
                )
            else:
                # Use schema-aware dynamic prompting
                prompt = self.prompt_generator.generate_schema_prompt(
                    description=description,
                    schema_name=schema_name,
                    count=count,
                    use_dspy=True
                )
            
            logger.info(f"Generated dynamic prompt for {schema_name} schema with {count} examples")
            return prompt
            
        except Exception as e:
            logger.warning(f"DSPy prompt generation failed, falling back to static prompt: {e}")
            # Fallback to static prompts
            return self._build_static_prompt(description, schema_name, count)
    
    def _build_static_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
    ) -> str:
        """Build static fallback prompt for generating examples from description."""
        schema_class = SchemaRegistry.get(schema_name)
        columns = schema_class.get_columns()
        
        prompts = {
            "alpaca": f"""Generate {count} high-quality instruction-tuning examples for the following task:
{description}

Format each example as a JSON object with these fields:
- instruction: The task or question
- input: Optional context or input (can be empty string)
- output: The expected response

Return a JSON array of {count} examples.
Example format:
[
  {{
    "instruction": "Translate the following text to French",
    "input": "Hello, how are you?",
    "output": "Bonjour, comment allez-vous?"
  }}
]""",
            
            "dolly": f"""Generate {count} high-quality instruction-tuning examples for the following task:
{description}

Format each example as a JSON object with these fields:
- instruction: The task or question
- context: Background information or constraints
- response: The expected answer
- category: Type of task (optional)

Return a JSON array of {count} examples.""",
            
            "sharegpt": f"""Generate {count} high-quality conversation examples for the following task:
{description}

Format each example as a JSON object with a "conversations" array:
[
  {{
    "conversations": [
      {{"from": "human", "value": "User message"}},
      {{"from": "gpt", "value": "Assistant response"}}
    ]
  }}
]

Return a JSON array of {count} conversation examples.""",
        }
        
        return prompts.get(schema_name, prompts["alpaca"])
    
    def _build_completion_prompt(
        self,
        row: pd.Series,
        schema_name: str,
    ) -> str:
        """Build prompt for completing a partial row."""
        # Get non-empty fields
        filled_fields = {}
        empty_fields = []
        
        for col, value in row.items():
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                empty_fields.append(col)
            else:
                filled_fields[col] = value
        
        prompt = f"""Complete the following {schema_name} format example.

Given fields:
{json.dumps(filled_fields, indent=2)}

Generate appropriate content for the missing fields: {', '.join(empty_fields)}

Return a JSON object with ONLY the missing fields and their values."""
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        schema_name: str,
    ) -> List[Dict[str, Any]]:
        """Parse AI response into dataset entries."""
        try:
            # Try to extract JSON from response
            parsed = extract_json_from_text(response)
            
            if not parsed:
                logger.warning("Could not parse JSON from response")
                return []
            
            # Ensure it's a list
            if isinstance(parsed, dict):
                parsed = [parsed]
            
            # Validate and convert entries
            dataset = []
            schema_class = SchemaRegistry.get(schema_name)
            
            for entry in parsed:
                try:
                    instance = schema_class.from_dict(entry)
                    if instance.validate_content():
                        dataset.append(instance.to_jsonl_entry())
                except Exception as e:
                    logger.warning(f"Invalid entry: {e}")
                    continue
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return []
    
    def _parse_completion_response(
        self,
        response: str,
        schema_name: str,
    ) -> Dict[str, Any]:
        """Parse completion response for partial row."""
        try:
            parsed = extract_json_from_text(response)
            
            if not parsed:
                return {}
            
            # Ensure it's a dictionary
            if isinstance(parsed, list) and parsed:
                parsed = parsed[0]
            
            if not isinstance(parsed, dict):
                return {}
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse completion: {e}")
            return {}
    
    @async_error_handler
    async def generate_from_csv(
        self,
        csv_path: Path,
        output_dir: Path,
        schema_name: str,
        max_rows: Optional[int] = None,
        batch_size: int = 10,
        delimiter: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Generate dataset from CSV template with partial data."""
        try:
            # Read CSV file
            df = CSVHandler.read_data(csv_path, delimiter=delimiter)
            
            # Validate schema compatibility
            is_valid, missing_cols = CSVHandler.validate_schema_compatibility(
                df, schema_name
            )
            if not is_valid:
                raise ValidationError(
                    f"CSV file missing required columns: {', '.join(missing_cols)}"
                )
            
            # Detect partial rows
            partial_rows = CSVHandler.detect_partial_rows(df)
            
            if not partial_rows:
                logger.info("No partial rows found. Converting existing data.")
                dataset = CSVHandler.convert_to_dataset(df, schema_name)
            else:
                # Limit rows if specified
                if max_rows:
                    partial_rows = partial_rows[:max_rows]
                
                logger.info(f"Found {len(partial_rows)} partial rows to complete")
                
                if dry_run:
                    logger.info("Dry run mode - skipping generation")
                    return {
                        "partial_rows": len(partial_rows),
                        "dry_run": True,
                    }
                
                # Generate completions for partial rows
                completed_data = await self._complete_partial_rows(
                    df,
                    partial_rows,
                    schema_name,
                    batch_size,
                )
                
                # Update DataFrame with completed data
                for idx, data in completed_data.items():
                    for key, value in data.items():
                        if key in df.columns:
                            df.at[idx, key] = value
                
                # Convert to dataset
                dataset = CSVHandler.convert_to_dataset(df, schema_name)
            
            # Write output
            output_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = output_dir / "data.jsonl"
            count = write_jsonl(dataset, jsonl_path)
            
            # Calculate metrics
            metrics = calculate_metrics(dataset, schema_name)
            
            # Save metadata
            metadata_path = save_metadata(
                output_dir,
                schema_name,
                self.model,
                count,
                {
                    "source": str(csv_path),
                    "temperature": self.temperature,
                    "seed": self.seed,
                },
                metrics,
            )
            
            # Write completed CSV if any rows were completed
            if partial_rows and not dry_run:
                completed_csv_path = output_dir / "completed_data.csv"
                CSVHandler.write_completed_data(
                    df,
                    completed_data,
                    completed_csv_path,
                    delimiter=delimiter or ','
                )
            
            logger.info(f"Successfully generated dataset with {count} examples")
            
            return {
                "row_count": count,
                "output_path": str(jsonl_path),
                "metadata_path": str(metadata_path),
                "metrics": metrics,
                "partial_rows": len(partial_rows),
            }
            
        except Exception as e:
            logger.error(f"Dataset generation failed: {e}")
            raise GenerationError(f"Failed to generate dataset: {str(e)}")
        
        finally:
            await self.client.close()
    
    def generate_from_csv_sync(
        self,
        csv_path: Path,
        output_dir: Path,
        schema_name: str,
        max_rows: Optional[int] = None,
        batch_size: int = 10,
        delimiter: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for CSV generation."""
        return asyncio.run(
            self.generate_from_csv(
                csv_path,
                output_dir,
                schema_name,
                max_rows,
                batch_size,
                delimiter,
                dry_run,
            )
        )