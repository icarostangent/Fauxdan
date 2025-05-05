from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import redis
import json
from internet.models import Host

class Command(BaseCommand):
    help = 'Enqueues hosts for domain enumeration. Use --target=all for all hosts or --target=<host_id> for a specific host.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target',
            type=str,
            required=True,
            help='Specify "all" to enqueue all hosts or provide a specific host ID'
        )

    def handle(self, *args, **options):
        target = options['target']

        try:
            # Connect to Redis
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )

            if target.lower() == 'all':
                # Process all hosts
                hosts = Host.objects.all()
                enqueued_count = 0

                for host in hosts:
                    data = {
                        'ip': host.ip,
                        'id': host.id
                    }
                    r.rpush(settings.REDIS_QUEUE_SSL_SCANNER, json.dumps(data))
                    enqueued_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully enqueued {enqueued_count} hosts for domain enumeration'
                    )
                )
            else:
                try:
                    # Process specific host
                    host_id = int(target)
                    host = Host.objects.get(id=host_id)
                    
                    data = {
                        'ip': host.ip,
                        'id': host.id
                    }
                    r.rpush(settings.REDIS_QUEUE_SSL_SCANNER, json.dumps(data))

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully enqueued host {host.ip} (ID: {host.id}) for domain enumeration'
                        )
                    )
                except ValueError:
                    raise CommandError('Host ID must be a number or "all"')
                except Host.DoesNotExist:
                    raise CommandError(f'Host with ID {target} does not exist')

        except Exception as e:
            raise CommandError(f'Error enqueueing host(s): {str(e)}')
