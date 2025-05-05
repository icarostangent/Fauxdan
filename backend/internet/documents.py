from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from internet.models import Host, Port, Domain


@registry.register_document
class PortDocument(Document):
    port_number = fields.IntegerField()
    proto = fields.TextField()
    status = fields.TextField()
    banner = fields.TextField()

    class Index:
        name = "ports"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = Port
        fields = []


@registry.register_document
class DomainDocument(Document):
    name = fields.TextField()
    source = fields.TextField()

    class Index:
        name = "domains"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = Domain
        fields = []


@registry.register_document
class HostDocument(Document):
    ip = fields.TextField()
    ports = fields.NestedField(doc_class=PortDocument)
    domains = fields.NestedField(doc_class=DomainDocument)
    
    class Index:
        name = "hosts"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = Host
        fields = []
