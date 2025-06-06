from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScanViewSet, HostViewSet, DomainViewSet, PortViewSet, ProxyViewSet, 
    DNSRelayViewSet, UniversalSearchView, CreateScanView, ElasticSearchView
)

router = DefaultRouter()
router.register(r'scans', ScanViewSet, basename='scans')
router.register(r'hosts', HostViewSet, basename='hosts')
router.register(r'domains', DomainViewSet, basename='domains')
router.register(r'ports', PortViewSet, basename='ports')
router.register(r'proxies', ProxyViewSet, basename='proxies')
router.register(r'dnsrelays', DNSRelayViewSet, basename='dnsrelays')

urlpatterns = [
    path('create-scan/', CreateScanView.as_view(), name='create-scan'),
    path('search/', UniversalSearchView.as_view(), name='universal-search'),
    # path('search/', ElasticSearchView.as_view(), name='elastic-search'),
    path('', include(router.urls)),
]
