#!/usr/bin/env python3
"""Test API response times to identify latency bottlenecks."""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import Config
from app.engine.openrouter_generator import OpenRouterGenerator

async def test_api_latency():
    """Test API response times with various prompt sizes."""
    config = Config.load()
    generator = OpenRouterGenerator(
        api_key=config.generator.api_key,
        model=config.generator.model,
        temperature=config.generator.temperature,
        max_tokens=config.generator.max_tokens,
        site_url=config.generator.site_url,
        site_name=config.generator.site_name,
        auto_fallback=True
    )
    
    print(f"\n{'='*80}")
    print(f"API Latency Test")
    print(f"{'='*80}")
    print(f"Model: {generator.model}")
    print(f"Temperature: {generator.temperature}")
    print(f"Max tokens: {generator.max_tokens}")
    print(f"{'='*80}\n")
    
    # Test cases with different prompt sizes
    test_cases = [
        {
            "name": "Small prompt",
            "system": "You are a helpful assistant.",
            "user": "Say hello.",
            "expected_tokens": 20
        },
        {
            "name": "Medium prompt",
            "system": "You are a creative story writer. Generate engaging narrative content.",
            "user": "Write a short paragraph about a forest.",
            "expected_tokens": 100
        },
        {
            "name": "Large prompt",
            "system": "You are an expert storyteller creating interactive fiction. Your responses should be vivid, immersive, and include multiple narrative perspectives. You must return valid JSON with specific fields.",
            "user": "Write a detailed scene set in an ancient library with 3 characters and atmospheric details. Include dialogue, sensory descriptions, and plot advancement. Format as JSON.",
            "expected_tokens": 500
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}: {test['name']}")
        print(f"{'─'*80}")
        
        sys_len = len(test['system'])
        user_len = len(test['user'])
        total_len = sys_len + user_len
        
        print(f"System prompt: {sys_len} chars")
        print(f"User prompt: {user_len} chars")
        print(f"Total: {total_len} chars (~{total_len//4} tokens estimated)")
        print(f"\nSending request...", end="", flush=True)
        
        start_time = time.time()
        try:
            response = await generator.generate(
                system_prompt=test['system'],
                user_prompt=test['user'],
                context_type="scene"
            )
            duration = time.time() - start_time
            
            print(f" ✓")
            print(f"Response time: {duration:.2f}s")
            
            if response.error:
                print(f"❌ Error: {response.error}")
            else:
                response_len = len(response.raw_response) if response.raw_response else 0
                print(f"Response length: {response_len} chars")
                if hasattr(response, 'text_blocks') and response.text_blocks:
                    print(f"Text blocks: {len(response.text_blocks)}")
            
            results.append({
                "test": test['name'],
                "duration": duration,
                "success": not response.error
            })
        
        except Exception as e:
            duration = time.time() - start_time
            print(f" ❌")
            print(f"Failed after {duration:.2f}s: {str(e)}")
            results.append({
                "test": test['name'],
                "duration": duration,
                "success": False
            })
        
        # Add delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"Summary")
    print(f"{'='*80}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        print(f"\n✅ Successful requests: {len(successful)}")
        avg_time = sum(r['duration'] for r in successful) / len(successful)
        min_time = min(r['duration'] for r in successful)
        max_time = max(r['duration'] for r in successful)
        
        print(f"   Average response time: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")
        print(f"   Range: {max_time - min_time:.2f}s")
        
        for result in successful:
            status = "✓" if result['success'] else "✗"
            print(f"   [{status}] {result['test']}: {result['duration']:.2f}s")
    
    if failed:
        print(f"\n❌ Failed requests: {len(failed)}")
        for result in failed:
            print(f"   [✗] {result['test']}: {result['duration']:.2f}s")
    
    print(f"\n{'='*80}")
    
    # Recommendations
    print("\n📊 Latency Analysis:")
    if results and successful:
        avg = sum(r['duration'] for r in successful) / len(successful)
        if avg < 10:
            print("✅ API latency is excellent (< 10s). Generation is fast.")
        elif avg < 20:
            print("⚠️  API latency is moderate (10-20s). Consider acceptable for interactive play.")
        elif avg < 40:
            print("⚠️  API latency is high (20-40s). May feel slow for players but workable.")
        else:
            print("❌ API latency is very high (> 40s). Consider:")
            print("   - Switching to a faster model")
            print("   - Using a different provider")
            print("   - Implementing request queuing/batching")

if __name__ == "__main__":
    asyncio.run(test_api_latency())
