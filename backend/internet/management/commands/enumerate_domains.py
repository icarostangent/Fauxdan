import socket
import dns.resolver
from OpenSSL import SSL, crypto
from django.core.management.base import BaseCommand
from django.db.models import Q
from internet.models import Host, Domain, Port, SSLCertificate
import time
from django.utils import timezone
from datetime import timedelta



class Command(BaseCommand):
    help = 'Enumerate domains associated with an IP address using reverse dns and ssl certificate analysis'

    def add_arguments(self, parser):
        parser.add_argument('--target', type=str, help='IP to check, or "all" to check all hosts with web ports')
        parser.add_argument('--ssl-only', action='store_true', help='Only check SSL certificate data')

    def handle(self, *args, **kwargs):
        ip = kwargs['target']
        ssl_only = kwargs.get('ssl_only', False)

        if ip.lower() == 'all':
            targets = Port.objects.filter(Q(port_number=80) | Q(port_number=443))
            self.stdout.write(self.style.SUCCESS(f'Found {len(targets)} web targets'))
        else:
            try:
                host = Host.objects.get(ip=ip)
                targets = host.ports.filter(Q(port_number=80) | Q(port_number=443))
                self.stdout.write(self.style.SUCCESS(f'Found {len(targets)} web ports for {ip}'))
            except Host.DoesNotExist:
                self.stdout.write(self.style.ERROR('Host does not exist in database.'))
                return

        # Process each target
        for target in targets:
            if target.last_seen and (timezone.now() - target.last_seen) < timedelta(weeks=2):
                self.stdout.write(f'Skipping {target.host} - last seen {target.last_seen}')
                continue

            self.stdout.write(f'Checking {target.host}...')
            target.last_seen = timezone.now()
            target.save()

            if not ssl_only:
                self._reverse_dns_lookup(target)
            
            if target.port_number == 443:
                self._ssl_cert_scan(target)

    def _reverse_dns_lookup(self, target):
        """Perform reverse DNS lookup and save results"""
        try:
            hostname = socket.gethostbyaddr(str(target.host))[0]
            domain, created = Domain.objects.get_or_create(
                name=hostname,
                host=target.host,
                defaults={'source': 'reverse_dns',}
            )
            if not created:
                domain.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'Found domain via reverse DNS: {hostname}'))
        except socket.herror:
            self.stdout.write(self.style.WARNING(f'No reverse DNS found for {target.host}'))

    def _ssl_cert_scan(self, target, port=443):
        """Extract domains from SSL certificate and save unique certificates"""
        sock = None
        conn = None
        try:
            # Initialize SSL context with default verification
            context = SSL.Context(SSL.TLS_METHOD)
            context.set_verify(SSL.VERIFY_NONE)
            
            # Create and configure socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((str(target.host), port))
            
            # Create SSL connection
            conn = SSL.Connection(context, sock)
            conn.set_tlsext_host_name(str(target.host).encode())  # Set SNI
            conn.set_connect_state()
            
            # Handle the handshake with a proper read/write loop and timeout
            start_time = time.time()
            while True:
                try:
                    conn.do_handshake()
                    break
                except (SSL.WantReadError, SSL.WantWriteError):
                    if time.time() - start_time > 5:
                        raise socket.timeout("Handshake timeout")
                    continue
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'SSL handshake failed for {target.host}:{port} - {str(e)}'))
                    return
            
            cert = conn.get_peer_certificate()
            
            if cert:
                # Convert to PEM format
                cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')
                cert_fingerprint = cert.digest('sha256').decode('utf-8')

                # Try to find existing certificate by fingerprint
                try:
                    ssl_cert = SSLCertificate.objects.get(fingerprint=cert_fingerprint)
                    
                    # Update the existing certificate's port and host references
                    ssl_cert.port = target
                    ssl_cert.host = target.host
                    ssl_cert.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'Updated port/host for existing certificate: {cert_fingerprint}'))
                    
                except SSLCertificate.DoesNotExist:
                    # Create new certificate if fingerprint not found
                    ssl_cert = SSLCertificate.objects.create(
                        fingerprint=cert_fingerprint,
                        pem_data=cert_pem,
                        subject_cn=cert.get_subject().CN,
                        issuer_cn=cert.get_issuer().CN,
                        valid_from=cert.get_notBefore().decode('utf-8'),
                        valid_until=cert.get_notAfter().decode('utf-8'),
                        port=target,
                        host=target.host,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Saved new SSL certificate: {cert_fingerprint}'))

                # Process domains from certificate
                subject = cert.get_subject()
                if subject.CN:
                    domain, created = Domain.objects.get_or_create(
                        name=subject.CN,
                        host=target.host,
                        defaults={'source': 'ssl_cn',}
                    )
                    if not created:
                        domain.save()
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Found domain via SSL CN: {subject.CN}'))

                # Get Subject Alternative Names
                for i in range(cert.get_extension_count()):
                    ext = cert.get_extension(i)
                    if 'subjectAltName' in str(ext.get_short_name()):
                        sans = str(ext).replace('DNS:', '').split(',')
                        for san in sans:
                            san = san.strip()
                            if san:
                                domain, created = Domain.objects.get_or_create(
                                    name=san,
                                    host=target.host,
                                    defaults={'source': 'ssl_san',}
                                )
                                if not created:
                                    domain.save()
                                if created:
                                    self.stdout.write(self.style.SUCCESS(f'Found domain via SSL SAN: {san}'))
        
        except socket.timeout:
            self.stdout.write(self.style.WARNING(f'Connection timeout for {target.host}:{port}'))
        except socket.error as e:
            self.stdout.write(self.style.WARNING(f'Socket error for {target.host}:{port} - {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'SSL cert scan failed for {target.host}:{port} - {str(e)}'))
        finally:
            # Clean up connections
            if conn:
                try:
                    conn.shutdown()
                except:
                    pass
                try:
                    conn.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass