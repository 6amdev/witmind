#!/usr/bin/env python3
"""
Test LLM Providers - ทดสอบว่า LLM provider ไหนใช้งานได้

Supports:
1. Claude (Anthropic API)
2. OpenRouter (Unified API)
3. Ollama (Local)
"""

import sys
import os
import logging
from pathlib import Path

# Add platform to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'platform'))

from core.llm_client import create_llm_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger('test')


def test_provider(provider: str, **kwargs):
    """Test a specific LLM provider"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {provider.upper()}")
    logger.info(f"{'='*60}")

    try:
        # Create client
        llm = create_llm_client(provider=provider, **kwargs)
        logger.info(f"✅ Client created")

        # Test simple chat
        logger.info("Sending test message...")
        response = llm.chat(
            messages=[{
                'role': 'user',
                'content': 'Say "Hello from {provider}!" in one sentence.'
            }],
            system='You are a helpful assistant.',
            max_tokens=100
        )

        logger.info(f"✅ Response received:")
        logger.info(f"   {response[:200]}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        return False


def check_api_keys():
    """Check which API keys are available"""
    logger.info("\n" + "="*60)
    logger.info("Checking API Keys")
    logger.info("="*60)

    keys = {
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
    }

    available = []
    for key_name, key_value in keys.items():
        if key_value and len(key_value) > 10:
            logger.info(f"✅ {key_name}: {key_value[:15]}...")
            available.append(key_name)
        else:
            logger.info(f"❌ {key_name}: Not set")

    return available


def main():
    """Main test function"""
    logger.info("="*60)
    logger.info("LLM Providers Test")
    logger.info("="*60)

    # Check API keys
    available_keys = check_api_keys()

    results = {}

    # Test OpenRouter (recommended)
    if 'OPENROUTER_API_KEY' in available_keys:
        logger.info("\n🌟 Testing OpenRouter (Recommended)")
        logger.info("Models available:")
        logger.info("  - anthropic/claude-3.5-sonnet (Smart, expensive)")
        logger.info("  - anthropic/claude-3-haiku (Fast, cheap)")
        logger.info("  - google/gemini-flash-1.5 (FREE)")
        logger.info("  - meta-llama/llama-3.2-3b-instruct (FREE)")

        # Test with free model
        results['openrouter_free'] = test_provider(
            'openrouter',
            model='google/gemini-flash-1.5'
        )

        # Test with Claude via OpenRouter
        results['openrouter_claude'] = test_provider(
            'openrouter',
            model='anthropic/claude-3.5-sonnet'
        )
    else:
        logger.warning("⚠️  OpenRouter API key not found")
        logger.info("   Get one at: https://openrouter.ai/keys")

    # Test Claude directly
    if 'ANTHROPIC_API_KEY' in available_keys:
        results['claude'] = test_provider('claude')
    else:
        logger.warning("⚠️  Anthropic API key not found")

    # Test Ollama (always try)
    logger.info("\n🖥️  Testing Ollama (Local)")
    results['ollama'] = test_provider(
        'ollama',
        base_url='http://localhost:11434',  # Try local first
        model='llama3.2'
    )

    if not results['ollama']:
        # Try Docker service name
        logger.info("   Trying Docker service...")
        results['ollama_docker'] = test_provider(
            'ollama',
            base_url='http://ollama:11434',
            model='llama3.2'
        )

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)

    working = [name for name, success in results.items() if success]
    failed = [name for name, success in results.items() if not success]

    if working:
        logger.info(f"✅ Working providers ({len(working)}):")
        for provider in working:
            logger.info(f"   - {provider}")
    else:
        logger.warning("⚠️  No working providers found!")

    if failed:
        logger.info(f"\n❌ Failed providers ({len(failed)}):")
        for provider in failed:
            logger.info(f"   - {provider}")

    # Recommendations
    logger.info("\n" + "="*60)
    logger.info("RECOMMENDATIONS")
    logger.info("="*60)

    if 'openrouter_free' in working:
        logger.info("✅ Use OpenRouter with FREE models for development:")
        logger.info("   llm = create_llm_client('openrouter', model='google/gemini-flash-1.5')")
    elif 'openrouter_claude' in working:
        logger.info("✅ Use OpenRouter with Claude:")
        logger.info("   llm = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')")
    elif 'claude' in working:
        logger.info("✅ Use Claude directly:")
        logger.info("   llm = create_llm_client('claude')")
    elif 'ollama' in working or 'ollama_docker' in working:
        logger.info("✅ Use Ollama (local, free):")
        url = 'http://ollama:11434' if 'ollama_docker' in working else 'http://localhost:11434'
        logger.info(f"   llm = create_llm_client('ollama', base_url='{url}')")
    else:
        logger.warning("⚠️  Setup required:")
        logger.info("   Option 1: Get OpenRouter key (has FREE models)")
        logger.info("             https://openrouter.ai/keys")
        logger.info("   Option 2: Start Ollama locally")
        logger.info("             docker compose up ollama")

    return len(working) > 0


if __name__ == '__main__':
    # Load .env if exists
    env_file = Path.home() / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

    success = main()
    sys.exit(0 if success else 1)
