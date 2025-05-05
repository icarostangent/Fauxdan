from rest_framework import serializers
from internet.models import Scan, Host, Domain, Port, Proxy, DNSRelay, SSLCertificate


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = '__all__'


class SSLCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSLCertificate
        fields = '__all__'


class PortSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField()

    class Meta:
        model = Port
        fields = '__all__'


class ProxySerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = '__all__'


class DomainSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField()

    class Meta:
        model = Domain
        fields = '__all__'


class HostSerializer(serializers.ModelSerializer):
    ports = PortSerializer(many=True)
    domains = DomainSerializer(many=True)
    ssl_certificates = SSLCertificateSerializer(many=True)

    class Meta:
        model = Host
        fields = '__all__'


class DNSRelaySerializer(serializers.ModelSerializer):
    port = PortSerializer()
    class Meta:
        model = DNSRelay
        fields = '__all__'
