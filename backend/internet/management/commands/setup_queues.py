"""
Management command to set up default queues
"""
from django.core.management.base import BaseCommand
from internet.models import JobQueue


class Command(BaseCommand):
    help = 'Set up default scanner job queues'
    
    def handle(self, *args, **options):
        # Create default queue
        default_queue, created = JobQueue.objects.get_or_create(
            name='default',
            defaults={
                'description': 'Default queue for scanner jobs',
                'max_concurrent_jobs': 5,
                'priority': 0,
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created default queue: {default_queue.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Default queue already exists: {default_queue.name}')
            )
        
        # Create high priority queue
        high_priority_queue, created = JobQueue.objects.get_or_create(
            name='high_priority',
            defaults={
                'description': 'High priority queue for urgent scanner jobs',
                'max_concurrent_jobs': 3,
                'priority': 10,
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created high priority queue: {high_priority_queue.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'High priority queue already exists: {high_priority_queue.name}')
            )
        
        # Create low priority queue
        low_priority_queue, created = JobQueue.objects.get_or_create(
            name='low_priority',
            defaults={
                'description': 'Low priority queue for background scanner jobs',
                'max_concurrent_jobs': 2,
                'priority': 1,  # Use positive priority values
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created low priority queue: {low_priority_queue.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Low priority queue already exists: {low_priority_queue.name}')
            )
        
        # Show all queues
        self.stdout.write('\nCurrent queues:')
        for queue in JobQueue.objects.all().order_by('-priority'):
            self.stdout.write(
                f'  {queue.name}: {queue.description} '
                f'(max: {queue.max_concurrent_jobs}, priority: {queue.priority}, enabled: {queue.enabled})'
            )
