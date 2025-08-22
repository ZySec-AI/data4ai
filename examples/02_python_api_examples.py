#!/usr/bin/env python3
"""
Python API Examples for Data4AI
These examples demonstrate how to use Data4AI programmatically in Python
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import data4ai
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_environment():
    """Check if required environment variables are set"""
    required_vars = ["OPENROUTER_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   export {var}='your-key-here'")
        return False

    print("✅ Environment variables are configured")
    return True


def example_1_quick_start():
    """Example 1: Quick start with simple generation"""
    print("\n🎯 Example 1: Quick Start")
    print("-" * 40)

    try:
        from data4ai import generate_from_description

        # Generate a simple dataset
        result = generate_from_description(
            description="Create 5 questions and answers about Python programming basics",
            repo="python-qa-example",
            dataset="alpaca",
            count=5,
            dry_run=True,  # Preview mode
        )

        print(f"✅ Would generate {result.get('count', 5)} examples")
        print("📁 Output would be saved to: data/python-qa-example/")
        print("📊 Schema: alpaca")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project directory")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_document_generation():
    """Example 2: Document-based generation"""
    print("\n📄 Example 2: Document-based Generation")
    print("-" * 40)

    try:
        from data4ai import generate_from_documents

        # Create a sample document for demonstration
        sample_doc = Path("sample_document.txt")
        sample_doc.write_text(
            """
        Python Programming Basics

        Python is a high-level, interpreted programming language known for its
        simplicity and readability. Key concepts include:

        1. Variables and Data Types
        2. Control Structures (if, for, while)
        3. Functions and Classes
        4. Error Handling
        5. File I/O Operations
        """
        )

        # Generate from the document
        result = generate_from_documents(
            document_path=str(sample_doc),
            repo="document-qa",
            dataset="chatml",
            count=10,
            taxonomy="basic",
            dry_run=True,
        )

        print(f"✅ Would generate {result.get('count', 10)} Q&A pairs from document")
        print(f"📁 Source document: {sample_doc}")
        print("📊 Schema: chatml (conversation format)")

        # Clean up
        sample_doc.unlink(missing_ok=True)

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_object_oriented_api():
    """Example 3: Object-oriented API usage"""
    print("\n🏗️ Example 3: Object-Oriented API")
    print("-" * 40)

    try:
        from data4ai import Data4AI

        # Initialize with custom configuration
        ai = Data4AI(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            openrouter_model="openai/gpt-4o-mini",
            temperature=0.8,
            hf_token=os.getenv("HF_TOKEN"),
            hf_org=os.getenv("HF_ORG", "YourOrg"),
        )

        # Generate dataset
        result = ai.generate_from_description(
            description="Create examples of Python code reviews and feedback",
            repo="python-reviews",
            dataset="alpaca",
            count=25,
            dry_run=True,
        )

        print(f"✅ Would generate {result.get('count', 25)} code review examples")
        print("🤖 Model: openai/gpt-4o-mini")
        print("🌡️ Temperature: 0.8")
        print("📊 Schema: alpaca")

        # Note: Publishing would require HF_TOKEN
        if os.getenv("HF_TOKEN"):
            print("📤 Could publish to HuggingFace (dry run)")
        else:
            print("📤 Set HF_TOKEN to enable HuggingFace publishing")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_batch_processing():
    """Example 4: Batch processing multiple datasets"""
    print("\n📦 Example 4: Batch Processing")
    print("-" * 40)

    try:
        from data4ai import (
            generate_from_description,  # noqa: F401 - Used in commented code below
        )

        # Define multiple datasets to generate
        datasets = [
            {
                "description": "Create cooking recipe instructions with ingredients",
                "repo": "cooking-recipes",
                "count": 20,
                "taxonomy": "basic",
                "dataset": "alpaca",
            },
            {
                "description": "Create math word problems for middle school",
                "repo": "math-problems",
                "count": 30,
                "taxonomy": "balanced",
                "dataset": "alpaca",
            },
            {
                "description": "Create programming interview questions",
                "repo": "interview-qa",
                "count": 25,
                "taxonomy": "advanced",
                "dataset": "chatml",
            },
        ]

        print("📋 Batch processing configuration:")
        total_examples = 0

        for i, dataset in enumerate(datasets, 1):
            print(f"\n   Dataset {i}: {dataset['repo']}")
            print(f"   Description: {dataset['description']}")
            print(f"   Count: {dataset['count']} examples")
            print(f"   Taxonomy: {dataset['taxonomy']}")
            print(f"   Schema: {dataset['dataset']}")

            total_examples += dataset["count"]

            # In real usage, you would uncomment this:
            # result = generate_from_description(
            #     description=dataset["description"],
            #     repo=dataset["repo"],
            #     dataset=dataset["dataset"],
            #     count=dataset["count"],
            #     taxonomy=dataset["taxonomy"]
            # )
            # print(f"✅ Generated {result.row_count} rows for {dataset['repo']}")

        print(f"\n📊 Total: {total_examples} examples across {len(datasets)} datasets")
        print("💡 Remove this comment block to execute real generation")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_custom_configuration():
    """Example 5: Custom configuration and error handling"""
    print("\n⚙️ Example 5: Custom Configuration & Error Handling")
    print("-" * 40)

    try:
        from data4ai import generate_from_description
        from data4ai.exceptions import ConfigurationError, GenerationError

        # Set custom environment variables for this example
        custom_config = {
            "OPENROUTER_MODEL": "anthropic/claude-3-5-sonnet",
            "TEMPERATURE": "0.7",
        }

        print("🔧 Custom configuration:")
        for key, value in custom_config.items():
            print(f"   {key}: {value}")
            os.environ[key] = value

        try:
            # Generate with custom parameters
            result = generate_from_description(
                description="Create educational content about machine learning concepts",
                repo="ml-education",
                dataset="alpaca",
                count=15,
                temperature=0.7,
                taxonomy="balanced",
                batch_size=5,
                dry_run=True,
            )

            print(f"✅ Would generate {result.get('count', 15)} ML education examples")
            print(f"🤖 Model: {os.getenv('OPENROUTER_MODEL')}")
            print(f"🌡️ Temperature: {os.getenv('TEMPERATURE')}")

        except ConfigurationError as e:
            print(f"❌ Configuration error: {e}")
            print("💡 Check your API keys and settings")

        except GenerationError as e:
            print(f"❌ Generation error: {e}")
            print("💡 Try reducing batch size or count")

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Check the error details above")

    except ImportError as e:
        print(f"❌ Import error: {e}")


def example_6_schema_comparison():
    """Example 6: Comparing different schema formats"""
    print("\n📊 Example 6: Schema Format Comparison")
    print("-" * 40)

    schemas = {
        "alpaca": {
            "description": "Instruction-following format",
            "fields": ["instruction", "input", "output"],
            "use_case": "Fine-tuning instruction-following models",
        },
        "chatml": {
            "description": "Conversation format",
            "fields": ["messages"],
            "use_case": "Chat/dialogue model training",
        },
    }

    print("📋 Available schemas:")
    for schema_name, schema_info in schemas.items():
        print(f"\n   {schema_name.upper()}:")
        print(f"   • Description: {schema_info['description']}")
        print(f"   • Fields: {', '.join(schema_info['fields'])}")
        print(f"   • Use case: {schema_info['use_case']}")

    print("\n💡 Example usage:")
    print("   # For instruction-following:")
    print("   data4ai prompt --dataset alpaca ...")
    print("   # For conversations:")
    print("   data4ai prompt --dataset chatml ...")


def main():
    """Run all examples"""
    print("🚀 Data4AI Python API Examples")
    print("=" * 50)

    # Check environment first
    if not check_environment():
        print("\n💡 Set your API key to run the examples:")
        print("   export OPENROUTER_API_KEY='your-key-here'")
        return

    # Run examples
    try:
        example_1_quick_start()
        example_2_document_generation()
        example_3_object_oriented_api()
        example_4_batch_processing()
        example_5_custom_configuration()
        example_6_schema_comparison()

        print("\n" + "=" * 50)
        print("✅ All examples completed!")
        print("\n💡 Next steps:")
        print("   • Remove dry_run=True to generate real datasets")
        print("   • Set HF_TOKEN to publish to HuggingFace")
        print("   • Check the docs/ directory for documentation")

    except KeyboardInterrupt:
        print("\n\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error running examples: {e}")


if __name__ == "__main__":
    main()
