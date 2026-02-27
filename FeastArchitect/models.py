"""
Feast Architect - Simplified Django Models
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
import json


class FeastRepository(models.Model):
    """Main repository container for Feast architecture."""
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=500, default='/opt/feast/feature_repo')
    description = models.TextField(blank=True)
    default_owner = models.CharField(max_length=255, default='Data Platform Team')
    
    # Complete architecture stored as JSON (nodes, edges, canvas state)
    architecture_json = models.JSONField(
        default=dict,
        help_text="Complete diagram state including nodes, edges, positions",
        encoder=DjangoJSONEncoder
    )
    
    # Repository settings
    settings = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    
    # Sync tracking
    last_synced_at = models.DateTimeField(null=True, blank=True)
    json_hash = models.CharField(max_length=64, blank=True, help_text="MD5 hash of last saved JSON")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='repositories'
    )

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_node_count(self):
        """Count nodes from stored JSON."""
        nodes = self.architecture_json.get('nodes', {})
        return len(nodes) if isinstance(nodes, dict) else len(nodes)

    def get_edge_count(self):
        """Count edges from stored JSON."""
        return len(self.architecture_json.get('edges', []))


class DataSource(models.Model):
    """Data source with ownership and access tracking."""
    
    DATABASE_TYPES = [
        # Relational
        ('postgres', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('sqlserver', 'SQL Server'),
        ('oracle', 'Oracle'),
        ('sqlite', 'SQLite'),
        # NoSQL
        ('mongodb', 'MongoDB'),
        ('dynamodb', 'DynamoDB'),
        ('cassandra', 'Cassandra'),
        ('couchbase', 'Couchbase'),
        ('elasticsearch', 'Elasticsearch'),
        # Cloud Warehouses
        ('snowflake', 'Snowflake'),
        ('bigquery', 'BigQuery'),
        ('redshift', 'Redshift'),
        ('databricks', 'Databricks Delta Lake'),
        ('synapse', 'Azure Synapse'),
        # Streaming
        ('kafka', 'Apache Kafka'),
        ('kinesis', 'AWS Kinesis'),
        ('pulsar', 'Apache Pulsar'),
        ('eventhubs', 'Azure Event Hubs'),
        # Object Storage
        ('s3', 'Amazon S3 (Parquet)'),
        ('gcs', 'Google Cloud Storage'),
        ('azureblob', 'Azure Blob Storage'),
        ('minio', 'MinIO'),
        # In-Memory
        ('redis', 'Redis'),
        ('memcached', 'Memcached'),
        ('dragonfly', 'Dragonfly'),
        # Graph
        ('neo4j', 'Neo4j'),
        ('neptune', 'Amazon Neptune'),
        # Time-Series
        ('influxdb', 'InfluxDB'),
        ('timescaledb', 'TimescaleDB'),
        ('clickhouse', 'ClickHouse'),
        # Others
        ('couchdb', 'CouchDB'),
        ('rethinkdb', 'RethinkDB'),
        ('firebase', 'Firebase'),
        ('supabase', 'Supabase'),
    ]

    repository = models.ForeignKey(
        FeastRepository, 
        on_delete=models.CASCADE, 
        related_name='data_sources'
    )
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=50, choices=DATABASE_TYPES)
    
    # Ownership
    owned_by = models.CharField(max_length=255, default='Data Platform Team')
    access_process = models.TextField(blank=True, help_text="Steps to get access")
    
    # Connection
    connection_string = models.CharField(max_length=500, blank=True)
    topic = models.CharField(max_length=255, blank=True, help_text="For Kafka sources")
    
    # Feast integration
    feast_connection_type = models.CharField(
        max_length=50,
        default='batch',
        choices=[
            ('batch', 'Batch (FileSource)'),
            ('stream', 'Stream (KafkaSource)'),
            ('push', 'Push (PushSource)'),
            ('request', 'Request Source'),
        ],
        help_text="How this source connects to Feast"
    )
    
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    
    # Canvas position (stored in JSON, but denormalized for quick access)
    pos_x = models.FloatField(default=100)
    pos_y = models.FloatField(default=100)
    
    # Column security
    column_security = models.JSONField(
        default=dict,
        help_text="PII columns, masked columns, restricted columns",
        encoder=DjangoJSONEncoder
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['repository', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"

    @property
    def debezium_supported(self):
        """Check if database supports Debezium CDC."""
        debezium_dbs = [
            'postgres', 'mysql', 'sqlserver', 'oracle', 'mongodb', 
            'cassandra', 'couchbase', 'elasticsearch', 'redshift',
            'pulsar', 'eventhubs', 'neo4j', 'timescaledb', 'clickhouse',
            'couchdb', 'supabase'
        ]
        return self.kind in debezium_dbs

    @property
    def category(self):
        """Get database category."""
        categories = {
            'postgres': 'Relational', 'mysql': 'Relational', 
            'sqlserver': 'Relational', 'oracle': 'Relational', 
            'sqlite': 'Relational', 'mongodb': 'NoSQL', 
            'dynamodb': 'NoSQL', 'cassandra': 'NoSQL',
            'couchbase': 'NoSQL', 'elasticsearch': 'NoSQL',
            'snowflake': 'Cloud Warehouse', 'bigquery': 'Cloud Warehouse',
            'redshift': 'Cloud Warehouse', 'databricks': 'Cloud Warehouse',
            'synapse': 'Cloud Warehouse', 'kafka': 'Streaming', 
            'kinesis': 'Streaming', 'pulsar': 'Streaming',
            'eventhubs': 'Streaming', 's3': 'Object Storage', 
            'gcs': 'Object Storage', 'azureblob': 'Object Storage', 
            'minio': 'Object Storage', 'redis': 'In-Memory', 
            'memcached': 'In-Memory', 'dragonfly': 'In-Memory',
            'neo4j': 'Graph', 'neptune': 'Graph', 'influxdb': 'Time-Series', 
            'timescaledb': 'Time-Series', 'clickhouse': 'Time-Series',
            'couchdb': 'Document', 'rethinkdb': 'Document',
            'firebase': 'Mobile/Realtime', 'supabase': 'Backend-as-a-Service'
        }
        return categories.get(self.kind, 'Unknown')


class Entity(models.Model):
    """Feast entity definition."""
    repository = models.ForeignKey(
        FeastRepository, 
        on_delete=models.CASCADE, 
        related_name='entities'
    )
    name = models.CharField(max_length=255)
    join_key = models.CharField(max_length=255, default='id')
    
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    
    pos_x = models.FloatField(default=100)
    pos_y = models.FloatField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['repository', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (join: {self.join_key})"


class AuditLog(models.Model):
    """Audit trail for all changes."""
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, EXPORT, IMPORT
    resource_type = models.CharField(max_length=50)  # repository, datasource, entity, etc.
    resource_name = models.CharField(max_length=255)
    details = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp}: {self.user} {self.action} {self.resource_type}"


class LLMChatSession(models.Model):
    """Chat session for LLM conversations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='llm_sessions')
    repository = models.ForeignKey(
        FeastRepository, 
        on_delete=models.CASCADE, 
        related_name='llm_sessions',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, default="New Chat")
    context_json = models.JSONField(
        default=dict,
        help_text="Snapshot of repository state when chat started",
        encoder=DjangoJSONEncoder
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def get_message_count(self):
        return self.messages.count()


class LLMMessage(models.Model):
    """Individual message in a chat session."""
    session = models.ForeignKey(
        LLMChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ])
    content = models.TextField()
    query_type = models.CharField(max_length=50, blank=True, help_text="generate_code, optimize, etc.")
    
    # Token usage from Groq API
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Model used
    model = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
