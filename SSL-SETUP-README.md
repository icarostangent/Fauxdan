# Let's Encrypt SSL Setup with Docker

This project now uses the PhoenixNAP strategy for setting up Let's Encrypt SSL certificates with Docker. The setup follows the approach outlined in [this article](https://phoenixnap.com/kb/letsencrypt-docker#Step_2_Create_Docker_Compose_File).

## Architecture

The SSL setup consists of two main services:

1. **webserver** (nginx): Serves the application and handles SSL termination
2. **certbot**: Manages Let's Encrypt certificates

## Files Structure

```
├── docker-compose.prod.yml      # Main production compose file
├── nginx/
│   ├── conf/
│   │   └── app.conf            # Nginx configuration
│   └── Dockerfile              # Nginx container definition
├── certbot/
│   ├── www/                    # Webroot for ACME challenges
│   └── conf/                   # Certificate storage
├── ssl-renewer/                 # Automatic SSL renewal service
│   ├── Dockerfile              # SSL renewal container
│   ├── entrypoint.sh           # Service startup script
│   ├── renew-ssl.sh            # Renewal execution script
│   └── README.md               # Service documentation
├── setup-ssl.sh                # Initial SSL setup script
├── renew-ssl.sh                # Manual renewal script
└── ssl-renewal.env.example     # SSL renewal configuration
```

## Initial Setup

1. **Start the webserver** (HTTP only initially):
   ```bash
   docker-compose -f docker-compose.prod.yml up -d webserver
   ```

2. **Run the SSL setup script**:
   ```bash
   ./setup-ssl.sh fauxdan.io
   ```

   This script will:
   - Test webroot accessibility
   - Run certbot dry-run
   - Obtain real certificates
   - Update nginx configuration for HTTPS
   - Restart the webserver

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. To renew them:

```bash
./renew-ssl.sh
```

## Automatic Renewal

The production configuration now includes an **automatic SSL renewal service** that runs in a Docker container. No manual cron setup is required!

### How It Works

1. **Dedicated Service**: `ssl-renewer` container runs alongside other services
2. **Cron Integration**: Built-in cron daemon handles scheduling
3. **Automatic Execution**: Certificates are renewed at configurable intervals
4. **Zero Downtime**: Nginx reloads configuration automatically

### Configuration

Set renewal interval using environment variables:

```bash
# In your .env file or environment
SSL_RENEWAL_INTERVAL=0 12 * * *    # Daily at 12:00 PM
DOMAIN_NAME=fauxdan.io
COMPOSE_PROJECT_NAME=fauxdan
```

### Manual Renewal (if needed)

You can still manually renew certificates:

```bash
# Run the renewal script directly
./renew-ssl.sh

# Or execute in the renewal container
docker exec <project-name>-ssl-renewer-1 /usr/local/bin/renew-ssl.sh
```

## How It Works

1. **HTTP Phase**: Initially, nginx only serves HTTP on port 80 and handles ACME challenges
2. **Certificate Acquisition**: Certbot obtains certificates using the webroot method
3. **HTTPS Phase**: After certificates are obtained, nginx configuration is updated to include HTTPS on port 443
4. **Redirect**: All HTTP traffic is redirected to HTTPS

## Troubleshooting

- **Webroot not accessible**: Ensure the `certbot/www/` directory exists and has proper permissions
- **Certificate errors**: Check that your domain points to the correct server IP
- **Nginx reload issues**: Verify the SSL certificate paths in the configuration

## Security Features

- TLS 1.2 and 1.3 support
- Strong cipher suites
- Security headers (HSTS, X-Frame-Options, etc.)
- Automatic HTTP to HTTPS redirect

## Benefits of This Approach

- **Separation of concerns**: Certbot and nginx are separate services
- **Easy renewal**: Simple certificate renewal process
- **No downtime**: Nginx reload instead of restart
- **Standard approach**: Follows industry best practices
- **Easy debugging**: Clear separation between HTTP and HTTPS phases
