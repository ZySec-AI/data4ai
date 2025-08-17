#!/usr/bin/env python3
"""
DSPy Integration Example for Data4AI

This example demonstrates how to use DSPy for dynamic prompt generation
to create high-quality datasets with adaptive prompting.
"""

import os
import asyncio
from pathlib import Path
from data4ai.integrations.dspy_prompts import create_prompt_generator, SchemaAwarePromptGenerator
from data4ai.generator import DatasetGenerator
from data4ai.config import settings


def example_dspy_prompt_generation():
    """Example of using DSPy for dynamic prompt generation."""
    print("🚀 DSPy Integration Example")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Please set OPENROUTER_API_KEY environment variable")
        return
    
    # Create prompt generator with DSPy
    print("📝 Creating DSPy prompt generator...")
    prompt_generator = create_prompt_generator(
        model_name="meta-llama/llama-3-8b-instruct",
        use_dspy=True
    )
    
    # Example 1: Basic dynamic prompt generation
    print("\n1️⃣ Basic Dynamic Prompt Generation")
    print("-" * 30)
    
    description = "Create programming questions about Python functions"
    schema_name = "alpaca"
    count = 5
    
    prompt = prompt_generator.generate_schema_prompt(
        description=description,
        schema_name=schema_name,
        count=count,
        use_dspy=True
    )
    
    print(f"Description: {description}")
    print(f"Schema: {schema_name}")
    print(f"Count: {count}")
    print(f"Generated Prompt Length: {len(prompt)} characters")
    print(f"Prompt Preview: {prompt[:200]}...")
    
    # Example 2: Adaptive prompting with previous examples
    print("\n2️⃣ Adaptive Prompting with Examples")
    print("-" * 40)
    
    previous_examples = [
        {
            "instruction": "Write a Python function to calculate factorial",
            "input": "Input: n = 5",
            "output": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
        },
        {
            "instruction": "Create a function to reverse a string",
            "input": "Input: 'hello'",
            "output": "def reverse_string(s):\n    return s[::-1]"
        }
    ]
    
    adaptive_prompt = prompt_generator.generate_adaptive_prompt(
        description="Create more Python function examples",
        schema_name="alpaca",
        count=3,
        previous_examples=previous_examples
    )
    
    print(f"Previous Examples: {len(previous_examples)}")
    print(f"Adaptive Prompt Length: {len(adaptive_prompt)} characters")
    print(f"Adaptive Prompt Preview: {adaptive_prompt[:200]}...")
    
    # Example 3: Schema-specific prompting
    print("\n3️⃣ Schema-Specific Prompting")
    print("-" * 30)
    
    schemas = ["alpaca", "dolly", "sharegpt"]
    
    for schema in schemas:
        schema_prompt = prompt_generator.generate_schema_prompt(
            description="Create educational content about machine learning",
            schema_name=schema,
            count=3,
            use_dspy=True
        )
        
        print(f"{schema.upper()} Prompt Length: {len(schema_prompt)} characters")
        print(f"{schema.upper()} Preview: {schema_prompt[:150]}...")
        print()


def example_dataset_generation_with_dspy():
    """Example of generating datasets using DSPy prompts."""
    print("\n🎯 Dataset Generation with DSPy")
    print("=" * 40)
    
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Please set OPENROUTER_API_KEY environment variable")
        return
    
    # Create generator with DSPy enabled
    print("🔧 Creating dataset generator with DSPy...")
    generator = DatasetGenerator(
        model="meta-llama/llama-3-8b-instruct",
        temperature=0.7,
        seed=42
    )
    
    # Generate dataset using DSPy prompts
    print("📊 Generating dataset with dynamic prompts...")
    
    try:
        result = generator.generate_from_prompt_sync(
            description="Create 5 high-quality programming questions about data structures",
            output_dir=Path("outputs/dspy-example"),
            schema_name="alpaca",
            count=5,
            batch_size=3,
            dry_run=False
        )
        
        print(f"✅ Generated {result['row_count']} examples")
        print(f"📁 Output: {result['output_path']}")
        
        # Show metrics
        metrics = result.get("metrics", {})
        if metrics:
            print(f"📈 Completion Rate: {metrics.get('completion_rate', 0):.1%}")
            print(f"📏 Avg Instruction Length: {metrics.get('avg_instruction_length', 0):.0f}")
            print(f"📏 Avg Output Length: {metrics.get('avg_output_length', 0):.0f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_dspy_vs_static_comparison():
    """Compare DSPy vs static prompt generation."""
    print("\n⚖️ DSPy vs Static Prompt Comparison")
    print("=" * 40)
    
    # Create both generators
    dspy_generator = create_prompt_generator(use_dspy=True)
    static_generator = create_prompt_generator(use_dspy=False)
    
    description = "Create cooking recipe instructions"
    schema_name = "alpaca"
    count = 3
    
    # Generate prompts
    dspy_prompt = dspy_generator.generate_schema_prompt(
        description, schema_name, count, use_dspy=True
    )
    
    static_prompt = static_generator.generate_schema_prompt(
        description, schema_name, count, use_dspy=False
    )
    
    print(f"Description: {description}")
    print(f"Schema: {schema_name}")
    print(f"Count: {count}")
    print()
    
    print("🔮 DSPy Prompt:")
    print(f"Length: {len(dspy_prompt)} characters")
    print(f"Preview: {dspy_prompt[:300]}...")
    print()
    
    print("📝 Static Prompt:")
    print(f"Length: {len(static_prompt)} characters")
    print(f"Preview: {static_prompt[:300]}...")
    print()
    
    print("💡 Key Differences:")
    print("- DSPy prompts are dynamically generated based on the specific request")
    print("- DSPy can adapt to different schemas and requirements")
    print("- DSPy supports adaptive prompting with previous examples")
    print("- Static prompts use predefined templates")


async def example_async_dspy_generation():
    """Example of async DSPy prompt generation."""
    print("\n🔄 Async DSPy Generation")
    print("=" * 30)
    
    # Create async generator
    generator = DatasetGenerator(
        model="meta-llama/llama-3-8b-instruct",
        temperature=0.7
    )
    
    # Generate dataset asynchronously
    result = await generator.generate_from_prompt(
        description="Create 3 examples of creative writing prompts",
        output_dir=Path("outputs/async-dspy-example"),
        schema_name="alpaca",
        count=3,
        batch_size=3,
        dry_run=True  # Use dry-run for demo
    )
    
    print(f"✅ Async generation completed")
    print(f"📊 Would generate: {result.get('count', 0)} examples")


def main():
    """Run all DSPy integration examples."""
    print("🎉 Data4AI DSPy Integration Examples")
    print("=" * 50)
    
    # Example 1: Basic DSPy prompt generation
    example_dspy_prompt_generation()
    
    # Example 2: Dataset generation with DSPy
    example_dataset_generation_with_dspy()
    
    # Example 3: DSPy vs static comparison
    example_dspy_vs_static_comparison()
    
    # Example 4: Async generation
    print("\n🔄 Running async example...")
    asyncio.run(example_async_dspy_generation())
    
    print("\n✅ All examples completed!")
    print("\n📚 Next Steps:")
    print("1. Try different schemas (alpaca, dolly, sharegpt)")
    print("2. Experiment with adaptive prompting")
    print("3. Use --use-dspy flag in CLI commands")
    print("4. Check outputs/ directory for generated datasets")


if __name__ == "__main__":
    main()
