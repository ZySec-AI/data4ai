"""Core dataset generation engine."""

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Any, Optional, Union

from data4ai.client import OpenRouterClient, OpenRouterConfig
from data4ai.config import settings
from data4ai.deduplicator import Deduplicator
from data4ai.document_handler import DocumentHandler
from data4ai.error_handler import async_error_handler, check_environment_variables
from data4ai.exceptions import ConfigurationError, GenerationError, ValidationError
from data4ai.schemas import SchemaRegistry
from data4ai.utils import (
    calculate_metrics,
    extract_json_from_text,
    save_metadata,
    write_jsonl,
)


# Backwards-compatible, lazily-resolved factory used in tests
def create_prompt_generator(
    model_name: str = "openai/gpt-4o-mini", use_dspy: bool = True
):
    try:
        from data4ai.integrations.dspy_prompts import (
            create_prompt_generator as _create,
        )

        return _create(model_name=model_name, use_dspy=use_dspy)
    except Exception as e:
        # Fallback to a simple static generator if DSPy is unavailable
        logger = logging.getLogger("data4ai")
        logger.warning(f"Falling back to static prompt generator: {e}")

        class _Simple:
            def __init__(self, model_name: str):
                self.model_name = model_name

            def generate_schema_prompt(
                self, description: str, schema_name: str, count: int, **_: Any
            ) -> str:
                return f"Generate {count} {schema_name} examples: {description}"

        return _Simple(model_name)


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
            # Check environment variables and provide helpful messages
            check_environment_variables(required_for_operation=["OPENROUTER_API_KEY"])
            raise ConfigurationError(
                "OpenRouter API key is required for dataset generation"
            )

        self.model = model or settings.openrouter_model
        self.temperature = temperature or settings.temperature
        self.seed = seed or settings.seed

        # Set random seed if provided
        if self.seed:
            random.seed(self.seed)

        # Initialize API client with proper attribution and longer timeout for generation
        config = OpenRouterConfig(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            site_url=settings.site_url,
            site_name=settings.site_name,
            timeout=120,  # 2 minutes for generation tasks
        )
        self.client = OpenRouterClient(config)

        # Load schema registry
        self.schemas = SchemaRegistry()

        # Defer DSPy initialization to avoid importing heavy deps at import time
        self.document_prompt_optimizer = None

        # Default to static prompt generator (no DSPy). Can be upgraded later.
        self.prompt_generator = self._create_static_prompt_generator(self.model)

        # If configured to use DSPy, attempt to enable it, otherwise fall back
        if settings.use_dspy and not self.enable_dspy_prompt_generator():
            # Fallback to legacy DSPy integration factory (kept for tests)
            try:
                self.prompt_generator = create_prompt_generator(
                    model_name=self.model, use_dspy=True
                )
                logger.info("Using fallback DSPy prompt generator")
            except Exception as e:
                logger.warning(f"Failed to initialize DSPy prompt generator: {e}")

    @async_error_handler
    async def generate_from_prompt(
        self,
        description: str,
        output_dir: Path,
        schema_name: str,
        count: int = 100,
        batch_size: int = 10,
        dry_run: bool = False,
        taxonomy: Optional[str] = None,
        taxonomy_all_levels: bool = False,
    ) -> dict[str, Any]:
        """Generate dataset from natural language description."""
        try:
            if dry_run:
                logger.info(f"Dry run: Would generate {count} examples")
                return {"count": count, "dry_run": True}

            logger.info(f"Generating {count} examples from description")

            # Generate prompt once for the entire generation (batch-agnostic)
            logger.info("Generating prompt for entire dataset...")
            master_prompt = self._build_generation_prompt(
                description,
                schema_name,
                batch_size,  # Use batch_size instead of total count
                None,  # No previous examples for master prompt
            )

            # Append taxonomy requirements if requested
            if taxonomy or taxonomy_all_levels:
                tax_note = (
                    f"Bloom taxonomy: {taxonomy or 'balanced'}. Each example MUST include a 'taxonomy_level' field "
                    "with one of: ['remember','understand','apply','analyze','evaluate','create']."
                )
                master_prompt = f"{master_prompt}\n\n{tax_note}"

            # Track if DSPy was actually used for prompt generation
            prompt_type = "static"

            # Check if DSPy was used for the master prompt
            if (
                hasattr(self.prompt_generator, "generate_dynamic_prompt")
                or (
                    hasattr(self.prompt_generator, "optimizer")
                    and hasattr(
                        getattr(self.prompt_generator, "optimizer", object()),
                        "generate_dynamic_prompt",
                    )
                )
                or getattr(self.prompt_generator, "use_dspy", False)
            ):
                prompt_type = "dspy"

            # Generate in batches using the same master prompt (CONCURRENT)
            dataset = []
            prompts_used = []  # Track prompts for audit

            total_batches = (count + batch_size - 1) // batch_size
            logger.info(
                f"🚀 Starting concurrent processing of {total_batches} batches..."
            )

            # Create all batch tasks
            batch_tasks = []
            # Plan batch-level taxonomy targets if strict coverage requested
            level_cycle = [
                "remember",
                "understand",
                "apply",
                "analyze",
                "evaluate",
                "create",
            ]
            all_levels_plan: list[str] = []
            if taxonomy_all_levels:
                all_levels_plan = [
                    level_cycle[i % len(level_cycle)] for i in range(count)
                ]
            for batch_start in range(0, count, batch_size):
                batch_count = min(batch_size, count - batch_start)
                current_batch = batch_start // batch_size + 1

                # Store prompt for audit with clear separation of different prompt stages
                prompts_used.append(
                    {
                        "batch": current_batch,
                        "dspy_input": description,  # What DSPy receives
                        "dspy_prompt": master_prompt,  # What DSPy generates
                        "final_prompt": None,  # What's actually sent to server
                        "examples_requested": batch_count,
                        "prompt_type": prompt_type,
                    }
                )

                # Create async task for this batch
                batch_levels = None
                if taxonomy_all_levels:
                    batch_levels = all_levels_plan[
                        batch_start : batch_start + batch_count
                    ]
                task = self._process_batch_concurrent(
                    batch_num=current_batch,
                    total_batches=total_batches,
                    prompt=master_prompt,
                    batch_count=batch_count,
                    schema_name=schema_name,
                    taxonomy=taxonomy,
                    batch_levels=batch_levels,
                )
                batch_tasks.append(task)

            # Process all batches concurrently with rate limiting
            max_concurrent = min(5, len(batch_tasks))  # Limit to 5 concurrent requests
            logger.info(
                f"⚡ Running {len(batch_tasks)} batches in parallel (max {max_concurrent} concurrent)..."
            )

            semaphore = asyncio.Semaphore(max_concurrent)

            async def run_with_semaphore(task):
                async with semaphore:
                    return await task

            limited_tasks = [run_with_semaphore(task) for task in batch_tasks]
            batch_results = await asyncio.gather(*limited_tasks, return_exceptions=True)

            # Collect results and final prompts
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch {i + 1} failed with exception: {result}")
                else:
                    entries, final_prompt = result
                    dataset.extend(entries)
                    # Update the prompt info with the actual final prompt
                    prompts_used[i]["final_prompt"] = final_prompt

            logger.info(
                f"🎉 Concurrent processing complete! Generated {len(dataset)}/{count} examples ({(len(dataset) / count) * 100:.1f}%)"
            )

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
                "prompt_generation_method": prompt_type,
            }
            if taxonomy or taxonomy_all_levels:
                parameters["taxonomy"] = taxonomy or "balanced"
                parameters["taxonomy_all_levels"] = taxonomy_all_levels
            save_metadata(
                output_dir, schema_name, self.model, len(dataset), parameters, metrics
            )

            logger.info(f"Generated {len(dataset)} examples")

            return {
                "row_count": len(dataset),
                "output_path": str(jsonl_path),
                "metrics": metrics,
                "prompts_used": prompts_used,
                "prompt_generation_method": prompt_type,
            }

        except Exception as e:
            logger.error(f"Generation from prompt failed: {e}")
            raise GenerationError(f"Failed to generate from prompt: {str(e)}") from e

    def generate_from_prompt_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for generate_from_prompt."""
        return asyncio.run(self.generate_from_prompt(*args, **kwargs))

    async def _process_batch_concurrent(
        self,
        batch_num: int,
        total_batches: int,
        prompt: str,
        batch_count: int,
        schema_name: str,
        taxonomy: Optional[str] = None,
        batch_levels: Optional[list[str]] = None,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Process a single batch using DSPy prompt generation + API calls."""
        import time

        try:
            logger.info(
                f"🔄 Batch {batch_num}/{total_batches}: Generating prompt for {batch_count} examples..."
            )

            # Use provided prompt as the generation base and add batch-specific taxonomy hints
            start_time = time.time()
            generation_prompt = prompt
            if taxonomy or batch_levels:
                generation_prompt += "\n\nOUTPUT REQUIREMENTS:\n- Each example MUST include a 'taxonomy_level' field with one of: ['remember','understand','apply','analyze','evaluate','create']."
                if batch_levels:
                    generation_prompt += f"\n- For this batch, assign taxonomy_level values in order: {batch_levels}."

            # Create system message for the schema
            system_message = self._get_system_prompt(schema_name)

            # Make API call with the generated prompt
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": generation_prompt},
            ]

            logger.info(
                f"📡 Batch {batch_num}/{total_batches}: Calling API with DSPy-optimized prompt..."
            )

            response = await self.client.chat_completion(
                messages=messages, temperature=self.temperature, max_tokens=4000
            )

            elapsed = time.time() - start_time

            # Parse the response
            response_text = response["choices"][0]["message"]["content"]
            entries = self._parse_response(response_text, schema_name, batch_count)
            # Fill in missing taxonomy labels if we have batch targets
            if batch_levels and entries:
                for i, e in enumerate(entries):
                    if "taxonomy_level" not in e:
                        e["taxonomy_level"] = batch_levels[i % len(batch_levels)]

            if entries:
                logger.info(
                    f"✅ Batch {batch_num}/{total_batches}: {len(entries)} valid entries generated in {elapsed:.1f}s"
                )
                return entries, {
                    "system_message": system_message,
                    "user_message": generation_prompt,
                }
            else:
                logger.error(
                    f"❌ Batch {batch_num}/{total_batches}: Failed to parse valid entries from response"
                )
                return [], {
                    "system_message": "Parse Error",
                    "user_message": generation_prompt,
                }

        except Exception as e:
            logger.error(
                f"❌ Batch {batch_num}/{total_batches}: Generation failed: {e}"
            )
            return [], {"system_message": "Exception", "user_message": str(e)}

    def _build_generation_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        previous_examples: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Build prompt for generating examples from description.

        Uses DSPy when available/enabled; otherwise falls back to a static prompt.
        """
        # Prefer DSPy paths when supported by the current prompt generator
        if hasattr(self.prompt_generator, "generate_dynamic_prompt"):
            logger.info(f"Using DSPy-centric prompt generation for {schema_name}")
            return self.prompt_generator.generate_dynamic_prompt(
                description=description,
                schema_name=schema_name,
                count=count,
                examples=previous_examples,
            )

        if hasattr(self.prompt_generator, "optimizer") and hasattr(
            self.prompt_generator.optimizer, "generate_dynamic_prompt"
        ):
            logger.info(
                f"Using DSPy-centric prompt generation via optimizer for {schema_name}"
            )
            return self.prompt_generator.optimizer.generate_dynamic_prompt(
                description=description,
                schema_name=schema_name,
                count=count,
                examples=previous_examples,
            )

        # Static fallback when DSPy is not enabled
        logger.info(f"Using static prompt generation for {schema_name}")
        return self.prompt_generator.generate_schema_prompt(
            description=description,
            schema_name=schema_name,
            count=count,
            use_dspy=False,
        )

    def _get_system_prompt(self, schema_name: str) -> str:
        """Get system prompt for generation."""
        base = "You are a dataset generator. Create training examples. Return ONLY valid JSON."

        if schema_name == "chatml":
            return f"{base} Each entry MUST have a 'messages' array with at least 2 messages."

        return base

    def _parse_response(
        self,
        response: str,
        schema_name: str,
        max_entries: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Parse AI response into dataset entries."""
        try:
            # Try to extract JSON from response
            parsed = extract_json_from_text(response)

            if not parsed:
                logger.warning("Could not parse JSON from response")
                return []

            # Pre-validate ChatML entries to catch empty messages arrays
            if schema_name == "chatml" and isinstance(parsed, list):
                for i, entry in enumerate(parsed):
                    if (
                        isinstance(entry, dict)
                        and "messages" in entry
                        and (not entry["messages"] or len(entry["messages"]) == 0)
                    ):
                        logger.warning(
                            f"Detected empty messages array in entry {i}, attempting to fix..."
                        )
                        fixed_entry = self._fix_empty_chatml_entry(entry, schema_name)
                        if fixed_entry:
                            parsed[i] = fixed_entry
                            logger.info(
                                f"Successfully fixed entry {i} with empty messages array"
                            )

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

                        # Limit the number of entries if specified
                        if max_entries and len(dataset) >= max_entries:
                            logger.info(
                                f"Limited to {max_entries} entries as requested"
                            )
                            break

                except Exception as e:
                    logger.warning(f"Invalid entry: {e}")
                    # Log the problematic entry for debugging
                    if (
                        "messages" in entry
                        and isinstance(entry["messages"], list)
                        and len(entry["messages"]) == 0
                    ):
                        logger.warning(
                            "Empty messages array detected - attempting to fix..."
                        )
                        # Try to fix empty messages array by creating a fallback entry
                        fixed_entry = self._fix_empty_chatml_entry(entry, schema_name)
                        if fixed_entry:
                            try:
                                instance = schema_class.from_dict(fixed_entry)
                                if instance.validate_content():
                                    dataset.append(instance.to_jsonl_entry())
                                    logger.info(
                                        "Successfully fixed empty messages array"
                                    )
                                    continue
                            except Exception as fix_error:
                                logger.warning(
                                    f"Failed to fix empty messages: {fix_error}"
                                )
                    continue

            return dataset

        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return []

    def _fix_empty_chatml_entry(
        self, entry: dict[str, Any], schema_name: str
    ) -> Optional[dict[str, Any]]:
        """Fix empty ChatML messages array by creating a fallback entry."""
        if schema_name != "chatml":
            return None

        if not (
            "messages" in entry
            and isinstance(entry["messages"], list)
            and len(entry["messages"]) == 0
        ):
            return None

        # Create contextual fallback based on the task
        fallback_conversations = [
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Can you help me understand this topic?",
                    },
                    {
                        "role": "assistant",
                        "content": "I'd be happy to help you understand this topic. Based on the information provided, let me explain the key concepts.",
                    },
                ]
            },
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "What are the main points I should know?",
                    },
                    {
                        "role": "assistant",
                        "content": "Here are the main points you should understand about this topic: The key concepts include proper methodology and practical applications.",
                    },
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": "How does this work in practice?"},
                    {
                        "role": "assistant",
                        "content": "In practice, this involves following established procedures and applying the concepts systematically to achieve the desired results.",
                    },
                ]
            },
        ]

        # Use a random fallback conversation
        import random

        fallback_entry = random.choice(fallback_conversations).copy()

        # Copy any additional fields from the original entry
        for key, value in entry.items():
            if key != "messages":
                fallback_entry[key] = value

        logger.info("Created contextual fallback ChatML entry for empty messages array")
        return fallback_entry

    @async_error_handler
    async def generate_from_document_dspy(
        self,
        document_path: Union[Path, str],
        output_dir: Path,
        schema_name: str = "chatml",
        objectives: Optional[dict] = None,
        budget: Optional[dict] = None,
        use_advanced: bool = False,
        recursive: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Generate dataset from document using DSPy plan→generate pipeline.

        This is the new budget-based generation that follows the DSPy plan.

        Args:
            document_path: Path to document or folder
            output_dir: Output directory
            schema_name: Dataset schema
            objectives: Dict with taxonomy, difficulty preferences
            budget: Dict with token_budget, min_examples, max_examples
            use_advanced: Use advanced extraction
            recursive: Scan folders recursively
            dry_run: Preview without generating

        Returns:
            Generation results with plan and metrics
        """
        if not self.document_prompt_optimizer:
            self._ensure_document_prompt_optimizer()
        if not self.document_prompt_optimizer:
            raise GenerationError(
                "DSPy document optimizer not initialized. "
                "Please ensure USE_DSPY=true and OPENROUTER_API_KEY is set."
            )

        # Default objectives and budget
        objectives = objectives or {"taxonomy": "balanced", "difficulty": "balanced"}
        budget = budget or {
            "token_budget": 10000,
            "min_examples": 10,
            "max_examples": 100,
        }

        # Extract full document text
        document_path = Path(document_path)
        if document_path.is_dir():
            # Handle folder input
            documents = DocumentHandler.scan_folder(document_path, recursive=recursive)
            if not documents:
                raise ValidationError(f"No documents found in {document_path}")
            # Combine all documents
            all_text = ""
            for doc_path in documents:
                text = DocumentHandler.extract_text(doc_path, use_advanced)
                all_text += f"\n\n=== {doc_path.name} ===\n\n{text}"
            document_text = all_text
        else:
            # Single document
            document_text = DocumentHandler.extract_text(document_path, use_advanced)

        if dry_run:
            logger.info("Dry run: Would create plan and generate with budget")
            return {
                "dry_run": True,
                "objectives": objectives,
                "budget": budget,
                "document_length": len(document_text),
            }

        # Step 1: Create generation plan
        logger.info("Step 1: Creating generation plan with DSPy")
        plan_dict = self.document_prompt_optimizer.plan(
            document_text=document_text,
            schema_name=schema_name,
            objectives=objectives,
            budget=budget,
        )

        # Get plan from LLM
        plan_prompt = plan_dict["prompt"]
        plan_response = await self.client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are a dataset planning expert. You MUST return ONLY valid JSON. No markdown, no code blocks, no explanations - just pure JSON output.",
                },
                {"role": "user", "content": plan_prompt},
            ],
            temperature=0.3,  # Lower temperature for planning
            max_tokens=2000,
        )

        plan_text = plan_response["choices"][0]["message"]["content"]
        generation_plan = extract_json_from_text(plan_text)

        if not generation_plan:
            raise GenerationError("Failed to create generation plan")

        logger.info(
            f"Plan created: {generation_plan.get('total_examples', 0)} examples across {len(generation_plan.get('sections', []))} sections"
        )

        # Step 2: Generate examples following the plan
        logger.info("Step 2: Generating examples following the plan")
        generate_prompt = self.document_prompt_optimizer.generate(
            document_text=document_text, schema_name=schema_name, plan=generation_plan
        )

        # Generate with higher token limit
        examples_response = await self.client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a dataset generator. Create {schema_name} format examples. You MUST return ONLY a valid JSON array. No markdown formatting, no code blocks, no explanations - just the JSON array.",
                },
                {"role": "user", "content": generate_prompt},
            ],
            temperature=self.temperature,
            max_tokens=4000,  # Higher limit for generation
        )

        examples_text = examples_response["choices"][0]["message"]["content"]
        dataset = self._parse_response(examples_text, schema_name)

        # Save results
        output_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = output_dir / "data.jsonl"
        write_jsonl(dataset, jsonl_path)

        # Calculate metrics
        metrics = calculate_metrics(dataset, schema_name)

        # Save metadata with plan
        parameters = {
            "source": str(document_path),
            "objectives": objectives,
            "budget": budget,
            "plan": generation_plan,
            "realized_count": len(dataset),
            "planned_count": generation_plan.get("total_examples", 0),
        }

        save_metadata(
            output_dir, schema_name, self.model, len(dataset), parameters, metrics
        )

        logger.info(
            f"Generated {len(dataset)} examples (planned: {generation_plan.get('total_examples', 0)})"
        )

        return {
            "row_count": len(dataset),
            "output_path": str(jsonl_path),
            "metrics": metrics,
            "plan": generation_plan,
            "realized_vs_planned": f"{len(dataset)}/{generation_plan.get('total_examples', 0)}",
        }

    async def generate_from_document(
        self,
        document_path: Path,
        output_dir: Path,
        schema_name: str,
        extraction_type: str = "qa",
        count: int = 100,
        batch_size: int = 10,
        chunk_size: int = 1000,
        chunk_tokens: Optional[int] = None,
        chunk_overlap: int = 200,
        taxonomy: Optional[str] = None,
        include_provenance: bool = False,
        taxonomy_all_levels: bool = True,
        verify_quality: bool = False,
        long_context: bool = False,
        use_advanced: bool = False,
        recursive: bool = True,
        dry_run: bool = False,
        dedup_strategy: str = "content",
        dedup_threshold: float = 0.97,
    ) -> dict[str, Any]:
        """Generate dataset from document(s) - supports files and folders.

        Args:
            document_path: Path to document file or folder
            output_dir: Output directory for dataset
            schema_name: Dataset schema (chatml, alpaca)
            extraction_type: Type of extraction (qa, summary, instruction)
            count: Number of examples to generate
            batch_size: Number of examples per batch
            chunk_size: Size of document chunks for processing
            use_advanced: Use advanced extraction methods
            recursive: For folders, scan recursively
            dry_run: Simulate without generation

        Returns:
            Generation results with metrics
        """
        try:
            logger.info(f"Preparing document for dataset generation: {document_path}")

            # Quick preflight connectivity check to avoid long hangs when offline
            try:
                preflight_messages = [
                    {"role": "system", "content": "You are a JSON-only responder."},
                    {"role": "user", "content": 'Return ["ok"]'},
                ]
                _ = await asyncio.wait_for(
                    self.client.chat_completion(
                        preflight_messages, temperature=0.0, max_tokens=5
                    ),
                    timeout=5.0,
                )
                logger.info("Connectivity preflight OK")
            except Exception as _e:
                raise GenerationError(
                    "Cannot reach the OpenRouter API (preflight failed within 5s). "
                    "Please check network connectivity or API credentials."
                ) from _e

            # Log quality features if enabled
            if any([taxonomy, verify_quality, long_context, chunk_tokens]):
                quality_features = []
                if taxonomy:
                    quality_features.append(f"taxonomy={taxonomy}")
                if verify_quality:
                    quality_features.append("verification")
                if long_context:
                    quality_features.append("long-context")
                if chunk_tokens:
                    quality_features.append(f"token-chunks={chunk_tokens}")
                logger.info(f"Quality features enabled: {', '.join(quality_features)}")

            # Use token-based chunking if specified
            if chunk_tokens:
                logger.info(
                    f"Using token-based chunking: {chunk_tokens} tokens per chunk"
                )
                # For now, approximate tokens to characters (will implement proper tokenizer later)
                chunk_size = chunk_tokens * 4  # Rough approximation: 1 token ≈ 4 chars

            # Prepare document(s) for generation - handles files and folders
            doc_data = DocumentHandler.prepare_for_generation(
                document_path,
                extraction_type=extraction_type,
                chunk_size=chunk_size,
                use_advanced=use_advanced,
                recursive=recursive,
            )

            if dry_run:
                logger.info(
                    f"Dry run: Would process {doc_data['total_chunks']} chunks from {doc_data.get('total_documents', 1)} document(s)"
                )
                return {
                    "document": doc_data.get("document_name")
                    or doc_data.get("document_names", ["multiple"])[0],
                    "chunks": doc_data["total_chunks"],
                    "total_documents": doc_data.get("total_documents", 1),
                    "dry_run": True,
                }

            # Log processing info
            if doc_data.get("total_documents", 1) > 1:
                logger.info(
                    f"Processing {doc_data['total_chunks']} chunks from {doc_data['total_documents']} documents"
                )
            else:
                logger.info(
                    f"Processing {doc_data['total_chunks']} chunks from {doc_data['document_type']} document"
                )

            # Generate examples from document chunks
            dataset: list[dict[str, Any]] = []
            chunks = doc_data["chunks"]

            # Check if we have folder structure to organize output
            folder_structure = doc_data.get("folder_structure")
            has_subfolders = folder_structure and folder_structure.get(
                "has_subfolders", False
            )

            # If we have subfolders, organize output by folder structure
            if has_subfolders:
                from collections import defaultdict

                def _merge_chunks_for_long_context(
                    group_chunks: list[dict[str, Any]],
                ) -> list[dict[str, Any]]:
                    if not long_context or len(group_chunks) <= 1:
                        return group_chunks
                    merged_chunks = []
                    current_merged = {"text": "", "ids": [], "start": 0, "end": 0}
                    max_context_chars = 8000
                    for chunk in group_chunks:
                        if (
                            len(current_merged["text"]) + len(chunk["text"])
                            < max_context_chars
                        ):
                            if current_merged["text"]:
                                current_merged["text"] += "\n\n"
                            current_merged["text"] += chunk["text"]
                            current_merged["ids"].append(chunk["id"])
                            current_merged["end"] = chunk["end"]
                            if not current_merged["start"]:
                                current_merged["start"] = chunk["start"]
                        else:
                            if current_merged["text"]:
                                merged_chunks.append(current_merged)
                            current_merged = {
                                "text": chunk["text"],
                                "ids": [chunk["id"]],
                                "start": chunk["start"],
                                "end": chunk["end"],
                            }
                    if current_merged["text"]:
                        merged_chunks.append(current_merged)
                    return [
                        {
                            "id": i,
                            "text": mc["text"],
                            "start": mc["start"],
                            "end": mc["end"],
                            "source": f"merged_chunks_{mc['ids']}",
                        }
                        for i, mc in enumerate(merged_chunks)
                    ]

                # group by file_path (added by extractor), fallback to source/doc name
                groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for ch in chunks:
                    key = ch.get("file_path") or ch.get("source") or "document"
                    groups[key].append(ch)

                total_rows = 0
                output_dir.mkdir(parents=True, exist_ok=True)

                # Process each document group sequentially (each group uses internal concurrency)
                for idx, (file_key, group_chunks) in enumerate(groups.items(), 1):
                    doc_name = Path(file_key).stem
                    logger.info(f"Processing document {idx}/{len(groups)}: {doc_name}")

                    group_chunks = _merge_chunks_for_long_context(group_chunks)

                    # Build a doc-level context (concat chunk texts up to limit) for coverage prompts
                    doc_context = []
                    total_len = 0
                    max_doc_ctx = 8000
                    for ch in group_chunks:
                        t = ch.get("text", "")
                        if total_len + len(t) <= max_doc_ctx:
                            doc_context.append(t)
                            total_len += len(t)
                        else:
                            break
                    doc_text_ctx = "\n\n".join(doc_context)

                    # Ensure all Bloom levels coverage for QA irrespective of count
                    baseline_entries: list[dict[str, Any]] = []
                    if extraction_type == "qa" and taxonomy_all_levels:
                        levels = [
                            "remember",
                            "understand",
                            "apply",
                            "analyze",
                            "evaluate",
                            "create",
                        ]

                        async def generate_level(
                            level: str,
                            chunks=group_chunks,
                            ctx=doc_text_ctx,
                            doc_name_local=doc_name,
                        ) -> list[dict[str, Any]]:
                            try:
                                # Base DSPy prompt for 1 example
                                base_prompt = self._build_document_qa_prompt(
                                    ctx or chunks[0]["text"],
                                    schema_name,
                                    1,
                                    taxonomy=taxonomy or "balanced",
                                    include_provenance=include_provenance,
                                )
                                # Enforce target level and label
                                level_spec = (
                                    f"\n\nADDITIONAL REQUIREMENTS:\n"
                                    f"- The question must target Bloom level: '{level}'.\n"
                                    f"- Include a 'taxonomy_level' field set to '{level}'.\n"
                                    f"- Return ONLY a JSON array with exactly 1 example."
                                )
                                prompt = base_prompt + level_spec

                                messages = [
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are a dataset generator. You MUST return ONLY a valid JSON array. "
                                            "No markdown, no explanations."
                                        ),
                                    },
                                    {"role": "user", "content": prompt},
                                ]
                                response = await asyncio.wait_for(
                                    self.client.chat_completion(
                                        messages,
                                        temperature=self.temperature,
                                        max_tokens=600,
                                    ),
                                    timeout=30.0,
                                )
                                response_text = response["choices"][0]["message"][
                                    "content"
                                ]
                                entries = self._parse_response(
                                    response_text, schema_name
                                )
                                # Add taxonomy label and source document tag
                                for e in entries or []:
                                    e.setdefault("taxonomy_level", level)
                                    e["source_document"] = f"{doc_name_local}"
                                return entries[:1] if entries else []
                            except Exception as e:
                                logger.warning(
                                    f"Failed to generate baseline level '{level}' for {doc_name_local}: {e}"
                                )
                                return []

                        # Run baseline coverage in parallel
                        baseline_results = await asyncio.gather(
                            *(generate_level(lv) for lv in levels),
                            return_exceptions=True,
                        )
                        for br in baseline_results:
                            if isinstance(br, Exception):
                                logger.warning(f"Baseline task failed: {br}")
                                continue
                            baseline_entries.extend(br or [])

                    # Determine per-chunk targets for this document (count applies per document)
                    examples_per_chunk = max(1, count // max(len(group_chunks), 1))
                    prompt_targets = [
                        min(examples_per_chunk, batch_size) for _ in group_chunks
                    ]
                    # Distribute target taxonomy levels across per-document chunks
                    levels_cycle_doc = [
                        "remember",
                        "understand",
                        "apply",
                        "analyze",
                        "evaluate",
                        "create",
                    ]
                    target_levels_doc = [
                        levels_cycle_doc[i % len(levels_cycle_doc)]
                        for i in range(len(group_chunks))
                    ]

                    max_concurrent = (
                        min(5, len(group_chunks)) if not long_context else 2
                    )
                    semaphore = asyncio.Semaphore(max_concurrent)

                    async def process_chunk_doc(
                        i_doc: int,
                        chunk_data: dict[str, Any],
                        levels=target_levels_doc,
                        sem=semaphore,
                        pc_targets=prompt_targets,
                    ) -> list[dict[str, Any]]:
                        chunk_text = chunk_data["text"]
                        prompt_count = pc_targets[i_doc]
                        # DSPy prompt based on extraction_type
                        if extraction_type == "qa":
                            prompt = self._build_document_qa_prompt(
                                chunk_text,
                                schema_name,
                                prompt_count,
                                taxonomy=taxonomy,
                                include_provenance=include_provenance,
                            )
                            # Require taxonomy_level label on each example
                            prompt += (
                                "\n\nOUTPUT REQUIREMENTS:\n"
                                "- Each example MUST include a 'taxonomy_level' field with one of: "
                                "['remember','understand','apply','analyze','evaluate','create'].\n"
                                f"- For this batch, taxonomy_level MUST be '{levels[i_doc]}'."
                            )
                        elif extraction_type == "summary":
                            prompt = self._build_document_summary_prompt(
                                chunk_text, schema_name, prompt_count
                            )
                        elif extraction_type == "instruction":
                            prompt = self._build_document_instruction_prompt(
                                chunk_text, schema_name, prompt_count
                            )
                        else:
                            prompt = self._build_document_general_prompt(
                                chunk_text, schema_name, prompt_count
                            )

                        schema_instructions = ""
                        if schema_name == "chatml":
                            schema_instructions = (
                                "\n\nCRITICAL CHATML REQUIREMENTS:\n"
                                '- Each entry MUST contain a "messages" array with at least 2 messages\n'
                                "- NEVER return empty messages arrays: []\n"
                                "- Always include user question and assistant response\n"
                            )
                        messages = [
                            {
                                "role": "system",
                                "content": (
                                    "You are a dataset generator. Create training examples based on the provided document content. "
                                    "You MUST respond with ONLY valid JSON arrays. No markdown, no code blocks, no explanations - just pure JSON output."
                                    f"{schema_instructions}"
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ]
                        async with sem:
                            try:
                                response = await asyncio.wait_for(
                                    self.client.chat_completion(
                                        messages,
                                        temperature=self.temperature,
                                        max_tokens=1500,
                                    ),
                                    timeout=30.0,
                                )
                                response_text = response["choices"][0]["message"][
                                    "content"
                                ]
                                entries = self._parse_response(
                                    response_text, schema_name
                                )
                                # Ensure taxonomy label present for QA
                                if extraction_type == "qa" and entries:
                                    for e in entries:
                                        if "taxonomy_level" not in e:
                                            e["taxonomy_level"] = levels[i_doc]
                                if verify_quality and entries:
                                    verified_entries = []
                                    for e in entries:
                                        v = await self._verify_and_improve_example(
                                            e, chunk_text, schema_name
                                        )
                                        verified_entries.append(v)
                                    entries = verified_entries
                                return entries
                            except asyncio.TimeoutError:
                                logger.error(
                                    f"⏰ Timeout processing chunk {i_doc} after 30s; skipping"
                                )
                                return []
                            except Exception as e:
                                logger.warning(
                                    f"Failed to generate from chunk {i_doc}: {e}"
                                )
                                return []

                    # Run group tasks
                    results = await asyncio.gather(
                        *(process_chunk_doc(i, c) for i, c in enumerate(group_chunks)),
                        return_exceptions=True,
                    )
                    group_entries: list[dict[str, Any]] = []
                    # Add baseline coverage first (may exceed 'count' as requested)
                    if baseline_entries:
                        group_entries.extend(baseline_entries)
                    for res in results:
                        if isinstance(res, Exception):
                            logger.warning(f"Chunk task failed: {res}")
                            continue
                        if res:
                            group_entries.extend(res)
                        # Do not trim early; user wants all levels irrespective of count
                    # Keep all baseline + chunk entries; no trim on count when taxonomy_all_levels

                    # Deduplicate per-document entries before writing
                    if group_entries:
                        try:
                            dedup = Deduplicator(
                                strategy=dedup_strategy, threshold=dedup_threshold
                            )
                            unique, stats = dedup.deduplicate(
                                group_entries, verbose=False
                            )
                            group_entries = unique
                            dedup_info = {
                                "dedup_method": stats.method,
                                "dedup_removed": stats.duplicates_removed,
                                "dedup_unique": stats.unique_items,
                                "dedup_total": stats.total_items,
                                "dedup_threshold": stats.threshold,
                            }
                        except Exception:
                            dedup_info = None
                    else:
                        dedup_info = None

                    # Write per-document output
                    doc_out_dir = output_dir / doc_name
                    doc_out_dir.mkdir(parents=True, exist_ok=True)
                    jsonl_path = doc_out_dir / "data.jsonl"
                    write_jsonl(group_entries, jsonl_path)
                    metrics = calculate_metrics(group_entries, schema_name)
                    if extraction_type == "qa":
                        from data4ai.utils import compute_taxonomy_coverage

                        metrics["taxonomy_coverage"] = compute_taxonomy_coverage(
                            group_entries
                        )
                    if dedup_info:
                        metrics.update(dedup_info)
                    params = {
                        "temperature": self.temperature,
                        "batch_size": batch_size,
                        "seed": self.seed,
                        "source": file_key,
                        "document_type": doc_data["document_type"],
                        "extraction_type": extraction_type,
                        "chunk_size": chunk_size,
                        "chunks_processed": len(group_chunks),
                        "total_documents": len(groups),
                        "input_type": doc_data.get("input_type", "file"),
                        "organized_by_folders": True,
                        "taxonomy_all_levels": (
                            taxonomy_all_levels if extraction_type == "qa" else False
                        ),
                    }
                    if chunk_tokens:
                        params["chunk_tokens"] = chunk_tokens
                    if taxonomy:
                        params["taxonomy"] = taxonomy
                    if include_provenance:
                        params["include_provenance"] = include_provenance
                    if verify_quality:
                        params["verify_quality"] = verify_quality
                    if long_context:
                        params["long_context"] = long_context

                    save_metadata(
                        doc_out_dir,
                        schema_name,
                        self.model,
                        len(group_entries),
                        params,
                        metrics,
                    )
                    total_rows += len(group_entries)

                # After creating folder-organized datasets, also create combined dataset
                logger.info("Creating combined dataset from all folders...")

                # Continue to create combined dataset below
                # Reset dataset to empty for combined processing
                dataset = []

            # Optional long-context merging
            if long_context and len(chunks) > 1:
                logger.info("Merging chunks for long-context processing...")
                merged_chunks = []
                current_merged = {"text": "", "ids": [], "start": 0, "end": 0}
                max_context_chars = 8000  # Conservative limit for most models

                for chunk in chunks:
                    if (
                        len(current_merged["text"]) + len(chunk["text"])
                        < max_context_chars
                    ):
                        # Add to current merged chunk
                        if current_merged["text"]:
                            current_merged["text"] += "\n\n"
                        current_merged["text"] += chunk["text"]
                        current_merged["ids"].append(chunk["id"])
                        current_merged["end"] = chunk["end"]
                        if not current_merged["start"]:
                            current_merged["start"] = chunk["start"]
                    else:
                        # Save current and start new
                        if current_merged["text"]:
                            merged_chunks.append(current_merged)
                        current_merged = {
                            "text": chunk["text"],
                            "ids": [chunk["id"]],
                            "start": chunk["start"],
                            "end": chunk["end"],
                        }

                if current_merged["text"]:
                    merged_chunks.append(current_merged)

                # Update chunks to use merged version
                chunks = [
                    {
                        "id": i,
                        "text": mc["text"],
                        "start": mc["start"],
                        "end": mc["end"],
                        "source": f"merged_chunks_{mc['ids']}",
                    }
                    for i, mc in enumerate(merged_chunks)
                ]
                logger.info(
                    f"Merged {doc_data['total_chunks']} chunks into {len(chunks)} long-context chunks"
                )

            # If combined mode with QA and all-levels requested, pre-generate coverage per document
            if (not has_subfolders) and extraction_type == "qa" and taxonomy_all_levels:
                from collections import defaultdict

                groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for ch in chunks:
                    key = ch.get("file_path") or ch.get("source") or "document"
                    groups[key].append(ch)

                levels = [
                    "remember",
                    "understand",
                    "apply",
                    "analyze",
                    "evaluate",
                    "create",
                ]

                async def baseline_for_doc(
                    group_chunks: list[dict[str, Any]],
                ) -> list[dict[str, Any]]:
                    # Build doc-level context
                    ctx_parts = []
                    total_len = 0
                    max_doc_ctx = 8000
                    for ch in group_chunks:
                        t = ch.get("text", "")
                        if total_len + len(t) <= max_doc_ctx:
                            ctx_parts.append(t)
                            total_len += len(t)
                        else:
                            break
                    doc_ctx = "\n\n".join(ctx_parts) or group_chunks[0]["text"]
                    doc_label = Path(
                        group_chunks[0].get("file_path")
                        or group_chunks[0].get("source")
                        or "document"
                    ).name

                    async def gen_level(level: str) -> list[dict[str, Any]]:
                        try:
                            base_prompt = self._build_document_qa_prompt(
                                doc_ctx,
                                schema_name,
                                1,
                                taxonomy=taxonomy or "balanced",
                                include_provenance=include_provenance,
                            )
                            base_prompt += (
                                "\n\nADDITIONAL REQUIREMENTS:\n"
                                f"- The question must target Bloom level: '{level}'.\n"
                                f"- Include a 'taxonomy_level' field set to '{level}'.\n"
                                "- Return ONLY a JSON array with exactly 1 example."
                            )
                            messages = [
                                {
                                    "role": "system",
                                    "content": "You are a dataset generator. Return ONLY valid JSON arrays.",
                                },
                                {"role": "user", "content": base_prompt},
                            ]
                            response = await asyncio.wait_for(
                                self.client.chat_completion(
                                    messages,
                                    temperature=self.temperature,
                                    max_tokens=600,
                                ),
                                timeout=30.0,
                            )
                            rt = response["choices"][0]["message"]["content"]
                            entries = self._parse_response(rt, schema_name)
                            # Tag entries with source_document
                            for e in entries or []:
                                e.setdefault("taxonomy_level", level)
                                e["source_document"] = doc_label
                            return entries[:1] if entries else []
                        except Exception as e:
                            logger.warning(f"Baseline level generation failed: {e}")
                            return []

                    results = await asyncio.gather(
                        *(gen_level(lv) for lv in levels), return_exceptions=True
                    )
                    out: list[dict[str, Any]] = []
                    for r in results:
                        if isinstance(r, Exception):
                            logger.warning(f"Baseline task failed: {r}")
                            continue
                        out.extend(r or [])
                    return out

                # Run baselines for all docs in combined mode
                baseline_all: list[dict[str, Any]] = []
                for group in groups.values():
                    baseline_all.extend(await baseline_for_doc(group))
                dataset.extend(baseline_all)

            examples_per_chunk = max(1, count // len(chunks)) if chunks else 0
            prompt_targets = [min(examples_per_chunk, batch_size) for _ in chunks]

            # Create taxonomy level targets for combined mode
            levels_cycle = [
                "remember",
                "understand",
                "apply",
                "analyze",
                "evaluate",
                "create",
            ]
            target_levels = [
                levels_cycle[i % len(levels_cycle)] for i in range(len(chunks))
            ]

            # Process chunks concurrently to avoid long sequential waits
            max_concurrent = min(5, len(chunks)) if not long_context else 2
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_chunk(
                idx: int, chunk_data: dict[str, Any]
            ) -> list[dict[str, Any]]:
                chunk_text = chunk_data["text"]
                prompt_count = prompt_targets[idx]

                # Add quality enhancements to prompt if enabled
                quality_instructions = []
                if taxonomy:
                    quality_instructions.append(
                        self._get_taxonomy_instruction(taxonomy)
                    )
                if include_provenance:
                    quality_instructions.append(
                        "Include source references with character offsets"
                    )

                # Log DSPy usage for document generation
                if self.document_prompt_optimizer and (
                    taxonomy or extraction_type != "qa"
                ):
                    logger.info(
                        f"Using DSPy-enhanced prompts for {extraction_type} generation"
                    )

                if extraction_type == "qa":
                    prompt = self._build_document_qa_prompt(
                        chunk_text,
                        schema_name,
                        prompt_count,
                        taxonomy=taxonomy,
                        include_provenance=include_provenance,
                    )
                    # Require taxonomy_level label on each example
                    prompt += (
                        "\n\nOUTPUT REQUIREMENTS:\n"
                        "- Each example MUST include a 'taxonomy_level' field with one of: "
                        "['remember','understand','apply','analyze','evaluate','create'].\n"
                        f"- For this batch, taxonomy_level MUST be '{target_levels[idx]}'."
                    )
                elif extraction_type == "summary":
                    prompt = self._build_document_summary_prompt(
                        chunk_text, schema_name, prompt_count
                    )
                elif extraction_type == "instruction":
                    prompt = self._build_document_instruction_prompt(
                        chunk_text, schema_name, prompt_count
                    )
                else:
                    prompt = self._build_document_general_prompt(
                        chunk_text, schema_name, prompt_count
                    )

                # Add schema-specific instructions for document generation
                schema_instructions = ""
                if schema_name == "chatml":
                    schema_instructions = """

CRITICAL CHATML REQUIREMENTS:
- Each entry MUST contain a "messages" array with at least 2 messages
- NEVER return empty messages arrays: []
- Always include user question and assistant response
- Example: {"messages": [{"role": "user", "content": "What is..."}, {"role": "assistant", "content": "Based on the document..."}]}"""

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a dataset generator. Create training examples based on the provided document content. "
                            "You MUST respond with ONLY valid JSON arrays. No markdown, no code blocks, no explanations - just pure JSON output."
                            f"{schema_instructions}"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]

                async with semaphore:
                    try:
                        logger.info(
                            f"🔄 Chunk {idx + 1}/{len(chunks)}: API call (timeout 30s)"
                        )
                        response = await asyncio.wait_for(
                            self.client.chat_completion(
                                messages,
                                temperature=self.temperature,
                                max_tokens=1500,
                            ),
                            timeout=30.0,
                        )
                        response_text = response["choices"][0]["message"]["content"]
                        entries = self._parse_response(response_text, schema_name)

                        # Tag entries with source_document for per-document reporting
                        src_doc = None
                        try:
                            src_doc = Path(
                                chunk_data.get("file_path")
                                or chunk_data.get("source")
                                or "document"
                            ).name
                        except Exception:
                            src_doc = "document"

                        for e in entries or []:
                            if src_doc:
                                e["source_document"] = src_doc

                        # Ensure taxonomy label present for QA
                        if extraction_type == "qa" and entries:
                            for e in entries:
                                if "taxonomy_level" not in e:
                                    e["taxonomy_level"] = "unspecified"

                        if verify_quality and entries:
                            verified_entries = []
                            for entry in entries:
                                v = await self._verify_and_improve_example(
                                    entry, chunk_text, schema_name
                                )
                                verified_entries.append(v)
                            entries = verified_entries

                        return entries
                    except asyncio.TimeoutError:
                        logger.error(
                            f"⏰ Timeout processing chunk {idx} after 30s; skipping"
                        )
                        return []
                    except Exception as e:
                        logger.warning(f"Failed to generate from chunk {idx}: {e}")
                        return []

            results = await asyncio.gather(
                *(process_chunk(i, c) for i, c in enumerate(chunks)),
                return_exceptions=True,
            )

            # Collect results and trim to requested count (skip trim when enforcing all-levels for QA)
            for res in results:
                if isinstance(res, Exception):
                    logger.warning(f"Chunk task failed: {res}")
                    continue
                if res:
                    dataset.extend(res)
                if (
                    not (
                        extraction_type == "qa"
                        and taxonomy_all_levels
                        and not has_subfolders
                    )
                    and len(dataset) >= count
                ):
                    break
            if not (
                extraction_type == "qa" and taxonomy_all_levels and not has_subfolders
            ):
                dataset = dataset[:count]

            # Deduplicate combined dataset before writing
            dedup_info = None
            if dataset:
                try:
                    dedup = Deduplicator(
                        strategy=dedup_strategy, threshold=dedup_threshold
                    )
                    unique, stats = dedup.deduplicate(dataset, verbose=False)
                    dataset = unique
                    dedup_info = {
                        "dedup_method": stats.method,
                        "dedup_removed": stats.duplicates_removed,
                        "dedup_unique": stats.unique_items,
                        "dedup_total": stats.total_items,
                        "dedup_threshold": stats.threshold,
                    }
                except Exception:
                    dedup_info = None

            # Write output
            output_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = output_dir / "data.jsonl"
            write_jsonl(dataset, jsonl_path)

            # Calculate metrics and taxonomy coverage (combined mode)
            metrics = calculate_metrics(dataset, schema_name)
            if extraction_type == "qa":
                from data4ai.utils import (
                    compute_taxonomy_by_document,
                    compute_taxonomy_coverage,
                )

                metrics["taxonomy_coverage_overall"] = compute_taxonomy_coverage(
                    dataset
                )
                metrics["taxonomy_coverage_by_document"] = compute_taxonomy_by_document(
                    dataset
                )
            if dedup_info:
                metrics.update(dedup_info)

            # Save metadata
            parameters = {
                "temperature": self.temperature,
                "batch_size": batch_size,
                "seed": self.seed,
                "source": str(document_path),
                "document_type": doc_data["document_type"],
                "extraction_type": extraction_type,
                "chunk_size": chunk_size,
                "chunks_processed": min(len(chunks), count),
                "total_documents": doc_data.get("total_documents", 1),
                "input_type": doc_data.get("input_type", "file"),
                "organized_by_folders": has_subfolders,
            }

            # Add quality parameters if used
            if chunk_tokens:
                parameters["chunk_tokens"] = chunk_tokens
            # Record taxonomy default for QA
            if extraction_type == "qa":
                parameters["taxonomy"] = taxonomy or "balanced"
                parameters["taxonomy_all_levels"] = taxonomy_all_levels
            if include_provenance:
                parameters["include_provenance"] = include_provenance
            if verify_quality:
                parameters["verify_quality"] = verify_quality
            if long_context:
                parameters["long_context"] = long_context

            # Add document names if multiple
            if doc_data.get("document_names"):
                parameters["documents"] = doc_data["document_names"][
                    :20
                ]  # Limit to 20 for metadata

            if extraction_type == "qa":
                parameters["taxonomy_all_levels"] = taxonomy_all_levels

            save_metadata(
                output_dir, schema_name, self.model, len(dataset), parameters, metrics
            )

            logger.info(
                f"Generated {len(dataset)} examples from {doc_data.get('total_documents', 1)} document(s)"
            )

            return {
                "row_count": len(dataset),
                "output_path": str(output_dir if has_subfolders else jsonl_path),
                "metrics": metrics,
                "document_type": doc_data["document_type"],
                "chunks_processed": min(len(chunks), count),
                "total_documents": doc_data.get("total_documents", 1),
                "organized_by_folders": has_subfolders,
            }

        except Exception as e:
            logger.error(f"Generation from document failed: {e}")
            raise GenerationError(f"Failed to generate from document: {str(e)}") from e

    def generate_from_document_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for document generation."""
        # Quick dry run check to avoid async/DSPy issues
        if kwargs.get("dry_run", False):
            document_path = args[0] if args else kwargs.get("document_path")
            if document_path:
                if hasattr(document_path, "is_dir") and document_path.is_dir():
                    from data4ai.document_handler import DocumentHandler

                    try:
                        docs = DocumentHandler.scan_folder(
                            document_path, recursive=kwargs.get("recursive", True)
                        )
                        total_docs = len(docs)
                        estimated_chunks = total_docs * 2  # Rough estimate
                    except Exception:
                        total_docs = 1
                        estimated_chunks = 2
                else:
                    total_docs = 1
                    estimated_chunks = 2  # Rough estimate for single doc

                return {
                    "document": (
                        document_path.name
                        if hasattr(document_path, "name")
                        else "document"
                    ),
                    "chunks": estimated_chunks,
                    "total_documents": total_docs,
                    "dry_run": True,
                }

        return asyncio.run(self.generate_from_document(*args, **kwargs))

    async def _verify_and_improve_example(
        self, example: dict, chunk_text: str, schema_name: str
    ) -> dict:
        """Verify example quality and improve if needed."""
        # Build verification prompt
        verify_prompt = f"""Review this generated example for quality:

Example: {json.dumps(example, indent=2)}

Source text: {chunk_text[:500]}...

Check:
1. Is the answer fully supported by the source text?
2. Is the question clear and answerable?
3. Are there any hallucinations or unsupported claims?

If there are issues, provide a corrected version. Otherwise, return the original.
Return ONLY a JSON object with the corrected or original example."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a quality reviewer for training data. You MUST respond with ONLY valid JSON. No markdown, no explanations - just the JSON object with corrected or verified examples.",
                },
                {"role": "user", "content": verify_prompt},
            ]

            response = await self.client.chat_completion(
                messages,
                temperature=0.1,  # Lower temperature for verification
                max_tokens=1000,
            )

            response_text = response["choices"][0]["message"]["content"]
            improved = extract_json_from_text(response_text)

            if improved and isinstance(improved, dict):
                return improved
            return example

        except Exception as e:
            logger.debug(f"Verification failed, keeping original: {e}")
            return example

    def _get_taxonomy_instruction(self, taxonomy: str) -> str:
        """Get instruction for Bloom's taxonomy levels (deprecated - DSPy handles this)."""
        # This method is deprecated - DSPy handles taxonomy instructions
        return ""

    def _build_document_qa_prompt(
        self,
        text: str,
        schema_name: str,
        count: int,
        taxonomy: Optional[str] = None,
        include_provenance: bool = False,
    ) -> str:
        """Build prompt for Q&A generation from document using DSPy."""

        if not self.document_prompt_optimizer:
            self._ensure_document_prompt_optimizer()
        if not self.document_prompt_optimizer:
            raise GenerationError(
                "DSPy document optimizer not initialized. "
                "Please ensure USE_DSPY=true and OPENROUTER_API_KEY is set."
            )

        logger.info(
            f"Using DSPy for document Q&A generation (taxonomy: {taxonomy or 'none'})"
        )

        # Always use DSPy for document Q&A generation
        prompt = self.document_prompt_optimizer.generate_taxonomy_prompt(
            document_text=text,
            schema_name=schema_name,
            count=count,
            taxonomy=taxonomy or "balanced",  # Default to balanced if not specified
            include_provenance=include_provenance,
        )
        # Remove old static prompt code - DSPy handles everything
        return prompt

    def _build_document_summary_prompt(
        self, text: str, schema_name: str, count: int
    ) -> str:
        """Build prompt for summary generation from document using DSPy."""

        if not self.document_prompt_optimizer:
            self._ensure_document_prompt_optimizer()
        if not self.document_prompt_optimizer:
            raise GenerationError(
                "DSPy document optimizer not initialized. "
                "Please ensure USE_DSPY=true and OPENROUTER_API_KEY is set."
            )

        logger.info("Using DSPy for document summary generation")

        # Always use DSPy for summary generation
        prompt = self.document_prompt_optimizer.generate_summary_prompt(
            document_text=text, schema_name=schema_name, count=count
        )
        return prompt

    def _build_document_instruction_prompt(
        self, text: str, schema_name: str, count: int
    ) -> str:
        """Build prompt for instruction generation from document using DSPy."""

        if not self.document_prompt_optimizer:
            self._ensure_document_prompt_optimizer()
        if not self.document_prompt_optimizer:
            raise GenerationError(
                "DSPy document optimizer not initialized. "
                "Please ensure USE_DSPY=true and OPENROUTER_API_KEY is set."
            )

    # --- Convenience configuration methods ---
    def use_static_prompt_generator(self) -> None:
        """Force the use of a static, non-DSPy prompt generator."""
        self.prompt_generator = self._create_static_prompt_generator(self.model)

    def enable_dspy_prompt_generator(self) -> bool:
        """Attempt to enable DSPy-based prompt generation. Returns True on success."""
        try:
            from data4ai.integrations.openrouter_dspy import (
                create_openrouter_prompt_generator,
            )

            self.prompt_generator = create_openrouter_prompt_generator(
                model=self.model, api_key=self.api_key
            )
            logger.info("Using OpenRouter DSPy integration for prompts")
            return True
        except Exception as e:
            logger.warning(f"Failed to enable DSPy prompt generator: {e}")
            return False

    def _ensure_document_prompt_optimizer(self) -> None:
        """Lazily initialize the DSPy document prompt optimizer if possible."""
        if self.document_prompt_optimizer is not None:
            return
        try:
            from data4ai.integrations.dspy_document_prompts import (
                create_document_prompt_optimizer,
            )

            self.document_prompt_optimizer = create_document_prompt_optimizer(
                model_name=self.model, use_dspy=True
            )
            logger.info("DSPy document prompt optimizer initialized successfully")
        except Exception as e:
            logger.warning(f"Cannot initialize DSPy document optimizer: {e}")
            self.document_prompt_optimizer = None

    # --- Static prompt generator (no DSPy dependency) ---
    class _SimplePromptGenerator:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def generate_schema_prompt(
            self, description: str, schema_name: str, count: int, **_: Any
        ) -> str:
            if schema_name == "chatml":
                return (
                    "You are a dataset generator. Create conversation examples in ChatML format.\n\n"
                    f"Generate {count} examples based on this description: {description}\n\n"
                    "CRITICAL REQUIREMENTS:\n"
                    '- Each entry MUST have a "messages" array with at least 2 messages (user + assistant)\n'
                    "- NEVER return empty messages arrays: []\n"
                    "- Return ONLY a valid JSON array with the requested number of examples"
                )
            else:
                return (
                    "You are a dataset generator. Create instruction-following examples (Alpaca format).\n\n"
                    f"Generate {count} examples based on this description: {description}\n\n"
                    "CRITICAL REQUIREMENTS:\n"
                    "- Each entry MUST include non-empty 'instruction' and 'output' fields\n"
                    "- 'input' may be an empty string when not needed\n"
                    "- Return ONLY a valid JSON array with the requested number of examples"
                )

    def _create_static_prompt_generator(
        self, model_name: str
    ) -> "DatasetGenerator._SimplePromptGenerator":
        return DatasetGenerator._SimplePromptGenerator(model_name)

    def _build_document_general_prompt(
        self, text: str, schema_name: str, count: int
    ) -> str:
        """Build general prompt for document-based generation using DSPy."""

        if not self.document_prompt_optimizer:
            raise GenerationError(
                "DSPy document optimizer not initialized. "
                "Please ensure USE_DSPY=true and OPENROUTER_API_KEY is set."
            )

        logger.info("Using DSPy for general document generation")

        # Use DSPy for general document generation
        prompt = self.document_prompt_optimizer.generate_general_prompt(
            document_text=text, schema_name=schema_name, count=count
        )
        return prompt
