"""
Management command to run tender extraction agents with 4 Agent Teams (V2)
使用4智能体团队增强的招标提取命令
"""
import asyncio
import logging
from asgiref.sync import sync_to_async
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crawler.models import CrawlSource, CrawlTask
from apps.crawler.agents import (
    TenderOrchestratorV2,
    OrchestratorV2Config,
    ConcurrencyConfig,
    RetryConfig,
    CacheConfig,
    FieldOptimizationConfig,
)
from apps.tenders.models import TenderNotice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run tender extraction agents with 4 Agent Teams (V2)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-id',
            type=int,
            help='Specific source ID to process'
        )
        parser.add_argument(
            '--source-name',
            type=str,
            help='Source name (partial match supported)'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=1,
            help='Maximum pages to crawl (default: 1)'
        )
        parser.add_argument(
            '--max-items',
            type=int,
            default=100,
            help='Maximum items per source (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run without saving to database'
        )
        parser.add_argument(
            '--no-cache',
            action='store_true',
            help='Disable caching'
        )
        parser.add_argument(
            '--no-field-opt',
            action='store_true',
            help='Disable field optimization (reduces LLM savings)'
        )
        parser.add_argument(
            '--concurrent-requests',
            type=int,
            default=5,
            help='Maximum concurrent HTTP requests (default: 5)'
        )
        parser.add_argument(
            '--concurrent-llm',
            type=int,
            default=2,
            help='Maximum concurrent LLM calls (default: 2)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Request delay in seconds (default: 1.0)'
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Only show statistics without running'
        )

    def handle(self, *args, **options):
        # Check if only stats requested
        if options.get('stats_only'):
            self.show_cache_stats()
            return

        # Run extraction
        asyncio.run(self.run_extraction(options))

    async def run_extraction(self, options: dict):
        """Run extraction with V2 orchestrator"""
        source_id = options.get('source_id')
        source_name = options.get('source_name')
        max_pages = options.get('max_pages', 1)
        max_items = options.get('max_items', 100)
        dry_run = options.get('dry_run', False)
        no_cache = options.get('no_cache', False)
        no_field_opt = options.get('no_field_opt', False)
        concurrent_requests = options.get('concurrent_requests', 5)
        concurrent_llm = options.get('concurrent_llm', 2)
        delay = options.get('delay', 1.0)

        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(self.style.NOTICE("  TenderOrchestratorV2 - 4 Agent Teams"))
        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(f"  Configuration:")
        self.stdout.write(f"    - Max pages: {max_pages}")
        self.stdout.write(f"    - Max items per source: {max_items}")
        self.stdout.write(f"    - Concurrent requests: {concurrent_requests}")
        self.stdout.write(f"    - Concurrent LLM calls: {concurrent_llm}")
        self.stdout.write(f"    - Request delay: {delay}s")
        self.stdout.write(f"    - Cache enabled: {not no_cache}")
        self.stdout.write(f"    - Field optimization: {not no_field_opt}")
        self.stdout.write(f"    - Dry run: {dry_run}")
        self.stdout.write("=" * 70)

        # Get sources (sync to async)
        sources = await self._get_sources(source_id, source_name)

        if not sources:
            self.stdout.write(self.style.ERROR("No active sources found"))
            return

        # Configure V2 orchestrator
        config = OrchestratorV2Config(
            # Concurrency settings
            max_concurrent_requests=concurrent_requests,
            max_concurrent_llm_calls=concurrent_llm,
            max_concurrent_details=concurrent_requests * 2,
            request_delay=delay,
            llm_delay=delay * 0.5,
            # Retry settings
            max_retries=3,
            base_delay=delay,
            circuit_breaker_threshold=5,
            # Cache settings
            cache_enabled=not no_cache,
            cache_ttl=7200,  # 2 hours
            # Field optimization
            use_list_data=not no_field_opt,
            use_regex_preprocessing=not no_field_opt,
            # Batch settings
            batch_size=20,
            max_items_per_source=max_items,
        )

        # Create V2 orchestrator
        orchestrator = TenderOrchestratorV2(config)

        total_extracted = 0
        total_cache_hits = 0
        total_llm_saved = 0
        total_llm_made = 0
        total_retries = 0

        start_time = datetime.now()

        for source in sources:
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(self.style.NOTICE(f"Processing source: {source.name}"))
            self.stdout.write(f"  URL: {source.base_url}")
            self.stdout.write(f"{'='*70}")

            # Create crawl task
            task = await self._create_task(source, max_pages, config)

            try:
                # Run V2 extraction
                results = await orchestrator.extract_tenders(source, max_pages=max_pages)

                # Save results
                saved_count = 0
                for result in results:
                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] {result.title[:60]}...")
                        saved_count += 1
                    else:
                        if await self._save_tender(result):
                            saved_count += 1

                # Update task
                await self._update_task(task, 'completed', saved_count)

                # Accumulate stats
                total_extracted += saved_count
                total_cache_hits += orchestrator.stats['cache_hits']
                total_llm_saved += orchestrator.stats['llm_calls_saved']
                total_llm_made += orchestrator.stats['llm_calls_made']
                total_retries += orchestrator.stats['retries']

                # Show source stats
                self.stdout.write(
                    self.style.SUCCESS(f"\n  Extracted {saved_count} tenders from {source.name}")
                )
                self._show_source_stats(orchestrator)

            except Exception as e:
                logger.error(f"Extraction failed for {source.name}: {e}")
                await self._update_task(task, 'failed', 0, str(e))

                self.stdout.write(
                    self.style.ERROR(f"\n  Failed to extract from {source.name}: {e}")
                )
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

        # Cleanup
        await orchestrator.close()

        # Final summary
        duration = (datetime.now() - start_time).total_seconds()
        self._show_final_summary(
            total_extracted,
            total_cache_hits,
            total_llm_saved,
            total_llm_made,
            total_retries,
            duration,
            len(sources)
        )

    def _show_source_stats(self, orchestrator):
        """Show statistics for current source"""
        stats = orchestrator.stats

        cache_total = stats['cache_hits'] + stats['cache_misses']
        cache_rate = stats['cache_hits'] / cache_total if cache_total > 0 else 0

        llm_total = stats['llm_calls_made'] + stats['llm_calls_saved']
        savings_rate = stats['llm_calls_saved'] / llm_total if llm_total > 0 else 0

        self.stdout.write(f"\n  Source Statistics:")
        self.stdout.write(f"    - Cache hits: {stats['cache_hits']} ({cache_rate:.1%})")
        self.stdout.write(f"    - LLM calls made: {stats['llm_calls_made']}")
        self.stdout.write(f"    - LLM calls saved: {stats['llm_calls_saved']} ({savings_rate:.1%})")
        self.stdout.write(f"    - Retries: {stats['retries']}")

    def _show_final_summary(self, total_extracted, cache_hits, llm_saved, llm_made, retries, duration, source_count):
        """Show final summary"""
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.SUCCESS("  FINAL SUMMARY"))
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"  Sources processed: {source_count}")
        self.stdout.write(f"  Total tenders extracted: {total_extracted}")
        self.stdout.write(f"  Total duration: {duration:.1f}s")
        if total_extracted > 0:
            self.stdout.write(f"  Average time per tender: {duration/total_extracted:.2f}s")
        self.stdout.write(f"\n  Agent Teams Performance:")
        self.stdout.write(f"    - CacheAgent hits: {cache_hits}")
        self.stdout.write(f"    - FieldOptimizer LLM savings: {llm_saved}")
        self.stdout.write(f"    - Total LLM calls: {llm_made}")
        self.stdout.write(f"    - RetryMechanism retries: {retries}")

        # Calculate savings rate
        llm_total = llm_saved + llm_made
        if llm_total > 0:
            savings_rate = llm_saved / llm_total
            self.stdout.write(f"\n  LLM Cost Savings: {savings_rate:.1%} ({llm_saved}/{llm_total} calls avoided)")

        self.stdout.write(f"{'='*70}")

    def show_cache_stats(self):
        """Show cache statistics"""
        from apps.crawler.agents import CacheAgent, CacheConfig

        cache_agent = CacheAgent(CacheConfig())
        stats = cache_agent.get_stats()

        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(self.style.NOTICE("  Cache Statistics"))
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"  Memory cache entries: {stats.total_memory_entries}")
        self.stdout.write(f"  Disk cache entries: {stats.total_disk_entries}")
        self.stdout.write(f"  Memory hit rate: {stats.memory_hit_rate:.2%}")
        self.stdout.write(f"  Overall hit rate: {stats.overall_hit_rate:.2%}")
        self.stdout.write(f"  Disk cache size: {stats.disk_cache_size_mb:.2f} MB")
        self.stdout.write(f"{'='*70}")

    @sync_to_async
    def _get_sources(self, source_id: int, source_name: str):
        """Get sources"""
        queryset = CrawlSource.objects.filter(status='active')

        if source_id:
            queryset = queryset.filter(id=source_id)
        elif source_name:
            queryset = queryset.filter(name__icontains=source_name)

        return list(queryset)

    @sync_to_async
    def _create_task(self, source, max_pages: int, config: OrchestratorV2Config):
        """Create crawl task"""
        return CrawlTask.objects.create(
            name=f"AgentV2 extraction - {source.name}",
            source_url=source.base_url,
            source_site=source.name,
            status='running',
            started_at=timezone.now(),
        )

    @sync_to_async
    def _update_task(self, task, status, items_crawled, error_message=None):
        """Update task"""
        task.status = status
        task.completed_at = timezone.now()
        task.items_crawled = items_crawled
        if error_message:
            task.error_message = error_message
        task.save()

    @sync_to_async
    def _save_tender(self, result) -> bool:
        """Save tender to database from V2 result"""
        try:
            # Convert schema to model fields
            fields = result.to_model_fields()

            # Check for existing
            existing = TenderNotice.objects.filter(
                source_url=fields['source_url']
            ).first()

            if existing:
                # Update
                for key, value in fields.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.save()
                self.stdout.write(f"  Updated: {fields['title'][:50]}...")
            else:
                # Create new
                TenderNotice.objects.create(**fields)
                self.stdout.write(f"  Created: {fields['title'][:50]}...")

            return True

        except Exception as e:
            logger.error(f"Failed to save tender: {e}")
            self.stdout.write(
                self.style.ERROR(f"  Failed to save: {e}")
            )
            return False
