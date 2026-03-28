"""
Test script for TenderAgent
"""
import asyncio
import os
import django
import logging

logging.basicConfig(level=logging.INFO)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.crawler.agents import TenderOrchestrator
from apps.crawler.agents.agents.url_analyzer import URLAnalyzerAgent
from apps.crawler.agents.agents.fetcher_agents import ListFetcherAgent
from apps.crawler.models import CrawlSource

async def test_step_by_step():
    """Test step by step"""
    print("Testing TenderAgent step by step...")

    # Get source
    source = await asyncio.to_thread(
        lambda: CrawlSource.objects.filter(id=3).first()
    )

    if not source:
        print("Source not found")
        return

    print(f"Source: {source.name}")

    # Step 1: Analyze
    print("\n[Step 1] Analyzing source...")
    analyzer = URLAnalyzerAgent()
    strategy = await asyncio.wait_for(
        asyncio.to_thread(analyzer._analyze_api_source, source),
        timeout=10
    )
    print(f"Strategy: {strategy.site_type}, max_pages={strategy.max_pages}")

    # Step 2: Fetch list
    print("\n[Step 2] Fetching list...")
    list_fetcher = ListFetcherAgent()
    try:
        items = await asyncio.wait_for(
            list_fetcher.fetch(strategy),
            timeout=30
        )
        print(f"Fetched {len(items)} items")
        if items:
            print(f"First item: {items[0].get('title', 'N/A')[:50]}...")
            print(f"URL: {items[0].get('url', 'N/A')}")
    except Exception as e:
        print(f"Error fetching list: {e}")

    # Step 3: Fetch detail
    print("\n[Step 3] Fetching detail page...")
    from apps.crawler.agents.agents.fetcher_agents import DetailFetcherAgent
    detail_fetcher = DetailFetcherAgent()
    try:
        detail = await asyncio.wait_for(
            detail_fetcher.fetch(items[0]),
            timeout=30
        )
        if detail:
            print(f"Detail page fetched: {len(detail.html)} bytes")
            print(f"Attachments: {len(detail.attachments)}")
        else:
            print("Failed to fetch detail")
    except Exception as e:
        print(f"Error fetching detail: {e}")
        import traceback
        traceback.print_exc()

    # Step 4: Extract fields
    print("\n[Step 4] Extracting fields...")
    from apps.crawler.agents.agents.field_extractor import FieldExtractorAgent
    extractor = FieldExtractorAgent()
    try:
        result = await asyncio.wait_for(
            extractor.extract(detail.html, detail.url),
            timeout=30
        )
        print(f"Extracted: {result.title[:60]}...")
        print(f"Tenderer: {result.tenderer or 'N/A'}")
        print(f"Budget: {result.budget_amount}")
        print(f"Method: {result.extraction_method}")
        print(f"Confidence: {result.extraction_confidence:.2f}")
    except Exception as e:
        print(f"Error extracting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_step_by_step())
