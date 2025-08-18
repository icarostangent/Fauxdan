# SSL Renewal Service

This service automatically renews Let's Encrypt SSL certificates at configurable intervals using cron jobs.

## Overview

The SSL renewal service runs in a dedicated Docker container and automatically:
- Checks for certificate expiration
- Renews certificates when needed
- Reloads nginx configuration to pick up new certificates
- Logs all renewal activities

## Configuration

### Environment Variables

Set these in your `.env` file or environment:

```bash
# SSL Renewal Interval (cron format)
SSL_RENEWAL_INTERVAL=0 12 * * *    # Daily at 12:00 PM

# Domain name for SSL certificates
DOMAIN_NAME=fauxdan.io

# Docker Compose project name
COMPOSE_PROJECT_NAME=fauxdan
```

### Renewal Intervals

Common cron patterns for SSL renewal:

| Pattern | Description |
|---------|-------------|
| `0 12 * * *` | Daily at 12:00 PM (recommended) |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `0 */6 * * *` | Every 6 hours |
| `0 0,12 * * *` | Twice daily at midnight and noon |

## How It Works

1. **Service Startup**: Container starts and waits for required services
2. **Cron Setup**: Configures cron job with specified interval
3. **Automatic Renewal**: Cron executes renewal script at scheduled times
4. **Certificate Renewal**: Uses certbot to renew certificates
5. **Nginx Reload**: Reloads nginx to pick up new certificates
6. **Logging**: Records all activities to log file

## Service Dependencies

The SSL renewal service depends on:
- `certbot` service (for certificate renewal)
- `nginx` service (for configuration reload)
- Docker socket access (for service communication)

## Logs

Renewal activities are logged to:
- Container logs: `docker logs <container-name>`
- Internal log file: `/var/log/ssl-renewal.log`

## Monitoring

Check service status:
```bash
# View service logs
docker logs <project-name>-ssl-renewer-1

# Check cron jobs
docker exec <project-name>-ssl-renewer-1 crontab -l

# Test renewal manually
docker exec <project-name>-ssl-renewer-1 /usr/local/bin/renew-ssl.sh
```

## Troubleshooting

### Common Issues

1. **Service not starting**: Check if certbot and nginx services are running
2. **Renewal failures**: Verify domain DNS configuration and Let's Encrypt rate limits
3. **Nginx reload failures**: Check nginx configuration syntax

### Debug Mode

Enable verbose logging by setting environment variable:
```bash
DEBUG=true
```

## Security

- Container runs with minimal privileges
- Only has access to necessary volumes and Docker socket
- Uses Alpine Linux for minimal attack surface
- Logs all activities for audit purposes

## Best Practices

1. **Renewal Frequency**: Set to daily to ensure certificates are always fresh
2. **Monitoring**: Check logs regularly for renewal status
3. **Backup**: Keep backup of SSL configuration
4. **Testing**: Test renewal process in staging environment first
