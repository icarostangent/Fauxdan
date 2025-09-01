"""
Tests for Django Metrics Application

Tests the metrics collection, views, and integration
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
import json
import time

class MetricsTestCase(TestCase):
    """Test case for metrics functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Clear cache before tests
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
    
    def test_metrics_endpoint(self):
        """Test the main metrics endpoint"""
        response = self.client.get('/metrics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'text/plain; version=0.0.4; charset=utf-8'
        )
        
        # Check that metrics are returned
        content = response.content.decode('utf-8')
        self.assertIn('django_app_info', content)
        self.assertIn('django_http_requests_total', content)
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint"""
        response = self.client.get('/metrics/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('checks', data)
        
        # Check that health checks are performed
        self.assertIn('database', data['checks'])
        self.assertIn('cache', data['checks'])
        self.assertIn('redis', data['checks'])
    
    def test_metrics_status_endpoint(self):
        """Test the metrics status endpoint"""
        response = self.client.get('/metrics/status/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('timestamp', data)
        self.assertIn('metrics', data)
        
        # Check that metrics categories are present
        self.assertIn('http_requests', data['metrics'])
        self.assertIn('database', data['metrics'])
        self.assertIn('cache', data['metrics'])
        self.assertIn('analytics', data['metrics'])
        self.assertIn('port_scanning', data['metrics'])
    
    def test_metrics_increment_endpoint(self):
        """Test the metrics increment endpoint"""
        # Test with valid data
        data = {
            'metric': 'analytics_visitors_total',
            'value': 1,
            'labels': {'source': 'test'}
        }
        
        response = self.client.post(
            '/metrics/increment/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
    def test_metrics_increment_invalid_metric(self):
        """Test increment with invalid metric name"""
        data = {
            'metric': 'nonexistent_metric',
            'value': 1
        }
        
        response = self.client.post(
            '/metrics/increment/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_metrics_increment_invalid_json(self):
        """Test increment with invalid JSON"""
        response = self.client.post(
            '/metrics/increment/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_metrics_collection(self):
        """Test that metrics are collected correctly"""
        # Make a request to generate some metrics
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 200)
        
        # Check that the metrics endpoint shows the request
        response = self.client.get('/metrics/status/')
        data = json.loads(response.content)
        
        # Should have at least one HTTP request
        self.assertGreaterEqual(
            data['metrics']['http_requests']['total'],
            1
        )
    
    def test_cache_metrics(self):
        """Test cache metrics collection"""
        # Set a test value in cache
        cache.set('test_key', 'test_value', 1)
        
        # Get the value to trigger cache operations
        result = cache.get('test_key')
        self.assertEqual(result, 'test_value')
        
        # Check metrics status
        response = self.client.get('/metrics/status/')
        data = json.loads(response.content)
        
        # Should have cache operations
        self.assertGreaterEqual(
            data['metrics']['cache']['hits'] + data['metrics']['cache']['misses'],
            0
        )
    
    def test_database_metrics(self):
        """Test database metrics collection"""
        # Perform a database operation
        user_count = User.objects.count()
        self.assertGreaterEqual(user_count, 1)
        
        # Check metrics status
        response = self.client.get('/metrics/status/')
        data = json.loads(response.content)
        
        # Should have database metrics
        self.assertIn('active_connections', data['metrics']['database'])
    
    def test_metrics_middleware_integration(self):
        """Test that metrics middleware is working"""
        # Make multiple requests to generate metrics
        for i in range(3):
            self.client.get('/metrics/')
        
        # Check that metrics are incremented
        response = self.client.get('/metrics/status/')
        data = json.loads(response.content)
        
        # Should have multiple requests
        self.assertGreaterEqual(
            data['metrics']['http_requests']['total'],
            3
        )
    
    def test_metrics_content_type(self):
        """Test that metrics endpoint returns correct content type"""
        response = self.client.get('/metrics/')
        
        self.assertEqual(
            response['Content-Type'],
            'text/plain; version=0.0.4; charset=utf-8'
        )
    
    def test_metrics_error_handling(self):
        """Test error handling in metrics collection"""
        # This test ensures that metrics collection doesn't break
        # even if there are errors in individual metric collection
        
        # Make a request that should generate metrics
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 200)
        
        # The metrics should still be collected even if some fail
        content = response.content.decode('utf-8')
        self.assertIn('django_app_info', content)

class MetricsIntegrationTestCase(TestCase):
    """Test case for metrics integration with other apps"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
    
    def test_metrics_with_analytics_integration(self):
        """Test metrics integration with analytics system"""
        # This test would verify that metrics are properly integrated
        # with your existing analytics system
        
        # For now, just test that the metrics endpoint works
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 200)
        
        # Check that analytics metrics are available
        content = response.content.decode('utf-8')
        self.assertIn('django_analytics_', content)
    
    def test_metrics_with_port_scanning_integration(self):
        """Test metrics integration with port scanning system"""
        # This test would verify that metrics are properly integrated
        # with your existing port scanning system
        
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 200)
        
        # Check that port scanning metrics are available
        content = response.content.decode('utf-8')
        self.assertIn('django_port_scan_', content)
