#!/usr/bin/env python3
"""
Example: Using OpenRouter API with proper attribution headers for analytics.

This example shows how to configure and use the OpenRouter client with
proper HTTP-Referer and X-Title headers for analytics and attribution.
"""

import os
import asyncio
from data4ai.client import OpenRouterConfig, OpenRouterClient, SyncOpenRouterClient


async def async_example():
    """Example using async OpenRouter client with attribution."""
    
    # Configuration with proper attribution
    config = OpenRouterConfig(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="meta-llama/llama-3-8b-instruct",
        temperature=0.7,
        site_url="https://www.zysec.ai",
        site_name="Data4AI"
    )
    
    client = OpenRouterClient(config)
    
    try:
        # Example messages
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant that creates high-quality training data."
            },
            {
                "role": "user", 
                "content": "Create a question and answer pair about machine learning."
            }
        ]
        
        print("Making async API call with attribution headers...")
        response = await client.chat_completion(messages)
        
        print(f"Response: {response['choices'][0]['message']['content']}")
        
        # Show usage information
        if 'usage' in response:
            usage = response['usage']
            print(f"Tokens used: {usage.get('total_tokens', 'N/A')}")
            print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        
    finally:
        await client.close()


def sync_example():
    """Example using sync OpenRouter client with attribution."""
    
    # Configuration with proper attribution
    config = OpenRouterConfig(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="meta-llama/llama-3-8b-instruct",
        temperature=0.7,
        site_url="https://www.zysec.ai",
        site_name="Data4AI"
    )
    
    client = SyncOpenRouterClient(config)
    
    try:
        # Example messages
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant that creates high-quality training data."
            },
            {
                "role": "user", 
                "content": "Create a question and answer pair about Python programming."
            }
        ]
        
        print("Making sync API call with attribution headers...")
        response = client.chat_completion(messages)
        
        print(f"Response: {response['choices'][0]['message']['content']}")
        
        # Show usage information
        if 'usage' in response:
            usage = response['usage']
            print(f"Tokens used: {usage.get('total_tokens', 'N/A')}")
            print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        
    finally:
        client.close()


async def list_models_example():
    """Example showing how to list available models."""
    
    config = OpenRouterConfig(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        site_url="https://www.zysec.ai",
        site_name="Data4AI"
    )
    
    client = OpenRouterClient(config)
    
    try:
        print("Fetching available models with attribution...")
        models = await client.list_models()
        
        print(f"Found {len(models)} available models:")
        for model in models[:5]:  # Show first 5 models
            print(f"  - {model['id']} ({model.get('context_length', 'N/A')} context)")
        
    finally:
        await client.close()


def show_headers_example():
    """Example showing the headers that will be sent."""
    
    config = OpenRouterConfig(
        api_key="your_api_key_here",
        site_url="https://www.zysec.ai",
        site_name="Data4AI"
    )
    
    client = SyncOpenRouterClient(config)
    
    # Show what headers will be sent
    headers = client._get_headers()
    print("Headers that will be sent to OpenRouter:")
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer [REDACTED]")
        else:
            print(f"  {key}: {value}")
    
    client.close()


if __name__ == "__main__":
    print("=== OpenRouter Attribution Example ===\n")
    
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY environment variable not set!")
        print("   Set it with: export OPENROUTER_API_KEY='your_key_here'")
        print("\nShowing header example without making API calls:\n")
        show_headers_example()
    else:
        print("1. Async example:")
        asyncio.run(async_example())
        
        print("\n" + "="*50 + "\n")
        
        print("2. Sync example:")
        sync_example()
        
        print("\n" + "="*50 + "\n")
        
        print("3. List models example:")
        asyncio.run(list_models_example())
        
        print("\n" + "="*50 + "\n")
        
        print("4. Headers example:")
        show_headers_example()
    
    print("\n=== Attribution Benefits ===")
    print("✅ Your API calls will be properly attributed to Data4AI")
    print("✅ Analytics will show usage from your project")
    print("✅ OpenRouter rankings will reflect Data4AI usage")
    print("✅ Better visibility for the project in the OpenRouter ecosystem")
