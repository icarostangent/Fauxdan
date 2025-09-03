#!/bin/bash

# Test ELK Stack Log Collection
echo "🧪 Testing ELK Stack Log Collection..."

# Test Elasticsearch connectivity through admin panel
echo "1️⃣ Testing Elasticsearch connectivity..."
if curl -f -k https://localhost:8443/elasticsearch/_cluster/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch is responding through admin panel"
    curl -s -k https://localhost:8443/elasticsearch/_cluster/health | jq '.'
else
    echo "❌ Elasticsearch is not responding through admin panel"
    exit 1
fi

# Test Kibana connectivity through admin panel
echo ""
echo "2️⃣ Testing Kibana connectivity..."
if curl -f -k https://localhost:8443/kibana/api/status > /dev/null 2>&1; then
    echo "✅ Kibana is responding through admin panel"
else
    echo "❌ Kibana is not responding through admin panel"
    exit 1
fi

# Generate test logs
echo ""
echo "3️⃣ Generating test logs..."

# Test Django application logs
echo "📝 Generating Django application logs..."
docker-compose -f docker-compose.dev.yml exec -T backend python -c "
import logging
import json
import time

# Configure logger
logger = logging.getLogger('fauxdan.test')
logger.setLevel(logging.DEBUG)

# Generate test logs
for i in range(10):
    logger.info(f'Test log message {i+1} - Application is running normally')
    logger.warning(f'Test warning {i+1} - This is a test warning message')
    if i % 3 == 0:
        logger.error(f'Test error {i+1} - This is a test error message')
    time.sleep(0.1)
"

# Test web server logs
echo "🌐 Generating web server logs..."
for i in {1..5}; do
    curl -s http://localhost/ > /dev/null
    curl -s http://localhost/api/ > /dev/null
    sleep 0.1
done

# Wait for logs to be processed
echo ""
echo "⏳ Waiting for logs to be processed by Logstash..."
sleep 10

# Check if logs are in Elasticsearch
echo ""
echo "4️⃣ Checking if logs are in Elasticsearch..."

# Check index exists
if curl -s -k https://localhost:8443/elasticsearch/_cat/indices/fauxdan-logs-* > /dev/null 2>&1; then
    echo "✅ Log indices found:"
    curl -s -k https://localhost:8443/elasticsearch/_cat/indices/fauxdan-logs-* | head -5
else
    echo "❌ No log indices found"
fi

# Count total logs
TOTAL_LOGS=$(curl -s -k https://localhost:8443/elasticsearch/fauxdan-logs-*/_count | jq '.count')
echo "📊 Total logs in Elasticsearch: $TOTAL_LOGS"

# Show sample logs
echo ""
echo "5️⃣ Sample logs from Elasticsearch:"
curl -s -k -X GET "https://localhost:8443/elasticsearch/fauxdan-logs-*/_search?size=3&sort=@timestamp:desc" | jq '.hits.hits[]._source | {timestamp: ."@timestamp", level: .log_level, message: .message, container: .container.name}'

echo ""
echo "🎉 ELK Stack test completed!"
echo ""
echo "📊 Next steps:"
echo "  1. Open Admin Panel: https://localhost:8443"
echo "  2. Click 'Open Kibana' to view logs"
echo "  3. Go to 'Discover' to view logs"
echo "  4. Go to 'Dashboard' to view the Application Logs dashboard"
echo "  5. Create custom visualizations as needed"
