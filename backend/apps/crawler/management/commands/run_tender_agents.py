"""
Management command to run tender extraction agents
"""
import asyncio
import logging
from asgiref.sync import sync_to_async

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crawler.models import CrawlSource, CrawlTask
from apps.crawler.agents import TenderOrchestrator
from apps.tenders.models import TenderNotice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run tender extraction agents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-id',
            type=int,
            help='Specific source ID to process'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=1,
            help='Maximum pages to crawl (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run without saving to database'
        )

    def handle(self, *args, **options):
        source_id = options.get('source_id')
        max_pages = options.get('max_pages', 1)
        dry_run = options.get('dry_run', False)

        asyncio.run(self.run_extraction(source_id, max_pages, dry_run))

    async def run_extraction(self, source_id: int, max_pages: int, dry_run: bool):
        """Run extraction"""
        self.stdout.write(self.style.NOTICE(f"Starting tender extraction (max_pages={max_pages})"))

        # Get sources (sync to async)
        sources = await self._get_sources(source_id)

        if not sources:
            self.stdout.write(self.style.ERROR("No active sources found"))
            return

        # Create orchestrator
        orchestrator = TenderOrchestrator()

        total_extracted = 0

        for source in sources:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.NOTICE(f"Processing source: {source.name}"))
            self.stdout.write(f"{'='*60}")

            # Create crawl task
            task = await self._create_task(source)

            try:
                # Run extraction
                results = await orchestrator.extract_tender(source, max_pages=max_pages)

                # Save results
                saved_count = 0
                for result in results:
                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] Would save: {result.title[:60]}...")
                        saved_count += 1
                    else:
                        if await self._save_tender(result):
                            saved_count += 1

                # Update task
                await self._update_task(task, 'completed', saved_count)

                total_extracted += saved_count

                self.stdout.write(
                    self.style.SUCCESS(f"Extracted {saved_count} tenders from {source.name}")
                )

            except Exception as e:
                logger.error(f"Extraction failed for {source.name}: {e}")
                await self._update_task(task, 'failed', 0, str(e))

                self.stdout.write(
                    self.style.ERROR(f"Failed to extract from {source.name}: {e}")
                )

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(
            self.style.SUCCESS(f"Total extracted: {total_extracted} tenders")
        )

    @sync_to_async
    def _get_sources(self, source_id: int):
        """Get sources"""
        if source_id:
            sources = list(CrawlSource.objects.filter(id=source_id, status='active'))
        else:
            sources = list(CrawlSource.objects.filter(status='active'))
        return sources

    @sync_to_async
    def _create_task(self, source):
        """Create crawl task"""
        return CrawlTask.objects.create(
            name=f"Agent extraction - {source.name}",
            source_url=source.base_url,
            source_site=source.name,
            status='running',
            started_at=timezone.now()
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
    def _save_tender(self, data) -> bool:
        """Save tender to database"""
        try:
            fields = data.to_model_fields()

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
