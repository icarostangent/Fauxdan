#!/bin/bash

# Start ELK Stack for Fauxdan Development
echo "🚀 Starting ELK Stack for Fauxdan Development..."

# Create log directories
echo "📁 Creating log directories..."
sudo mkdir -p /var/log/app
sudo chmod 755 /var/log/app

# Start ELK services
echo "🐳 Starting ELK services..."
docker-compose -f docker-compose.dev.yml up -d elasticsearch logstash kibana

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
until curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; do
    echo "Waiting for Elasticsearch..."
    sleep 5
done
echo "✅ Elasticsearch is ready!"

# Wait for Kibana to be ready
echo "⏳ Waiting for Kibana to be ready..."
until curl -f http://localhost:5601/api/status > /dev/null 2>&1; do
    echo "Waiting for Kibana..."
    sleep 5
done
echo "✅ Kibana is ready!"

# Create index pattern in Kibana
echo "📊 Creating index pattern in Kibana..."
curl -X POST "localhost:5601/api/saved_objects/index-pattern" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "title": "fauxdan-logs-*",
      "timeFieldName": "@timestamp"
    }
  }' > /dev/null 2>&1

echo "🎉 ELK Stack is ready!"
echo ""
echo "📊 Access URLs:"
echo "  - Admin Panel: https://localhost:8443"
echo "  - Kibana: https://localhost:8443/kibana"
echo "  - Elasticsearch: https://localhost:8443/elasticsearch"
echo "  - Logstash: https://localhost:8443/logstash"
echo ""
echo "📝 Log Sources:"
echo "  - Django Application: JSON structured logs"
echo "  - Caddy Web Server: JSON access logs"
echo "  - Docker Containers: Container logs"
echo "  - System Logs: Host system logs"
echo ""
echo "🔍 To view logs in Kibana:"
echo "  1. Go to https://localhost:8443"
echo "  2. Click 'Open Kibana' in the admin panel"
echo "  3. Navigate to 'Discover'"
echo "  4. Select 'fauxdan-logs-*' index pattern"
echo "  5. Start exploring your logs!"
